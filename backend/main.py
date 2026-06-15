import logging
import os
import tempfile

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import MAX_FILE_SIZE_MB, UPLOAD_DIR
from models import (
    AnalyzeRequest,
    AnalyzeResponse,
    LLMRequest,
    LLMResponse,
    Overview,
    PreprocessingPreview,
    PrimaryTaskSuggestion,
    ResearchPRDRequest,
    ResearchPRDResponse,
    ResearchPRDSuggestionsRequest,
    ResearchPRDSuggestionsResponse,
    UploadResponse,
)
from services.chart_data import build_eda_charts, generate_charts
from services.fingerprint import build_fingerprint
from services.llm import call_llm
from services.parser import get_preview, parse_file
from services.preprocessing import generate_preprocessing_previews
from services.research import generate_research_prd, get_research_suggestions
from services.profiler import compute_data_quality, profile_dataset
from services.task_suggestion import suggest_task
from storage import generate_dataset_id, get_dataset, store_dataset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AutoDataset Profiler API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(UPLOAD_DIR, exist_ok=True)


def _build_primary_suggestion(rule_suggestion, llm_understanding):
    if llm_understanding and llm_understanding.suggested_task in {
        "binary_classification", "multiclass_classification",
        "regression", "count_regression", "clustering_candidate",
    }:
        target_col = None
        confidence = None
        if llm_understanding.target_candidates:
            target_col = llm_understanding.target_candidates[0].column
            confidence = llm_understanding.target_candidates[0].confidence

        candidates = [
            {"column": tc.column, "reason": tc.reason, "confidence": tc.confidence}
            for tc in llm_understanding.target_candidates
        ] if llm_understanding.target_candidates else None

        return PrimaryTaskSuggestion(
            suggested_task=llm_understanding.suggested_task,
            reason=llm_understanding.task_reason,
            target_column=target_col,
            source="llm",
            confidence=confidence,
            target_candidates=candidates,
            domain_guess=llm_understanding.domain_guess,
        )

    return PrimaryTaskSuggestion(
        suggested_task=rule_suggestion.suggested_task,
        reason=rule_suggestion.reason,
        target_column=rule_suggestion.target_column,
        source="rule_based",
    )


@app.post("/api/datasets/upload", response_model=UploadResponse)
async def upload_dataset(file: UploadFile = File(...)):
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in (".csv", ".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload CSV or XLSX.",
        )

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)

    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {MAX_FILE_SIZE_MB} MB limit.",
        )

    safe_name = filename.replace(" ", "_")
    file_path = os.path.join(UPLOAD_DIR, f"upload_{safe_name}")

    with open(file_path, "wb") as f:
        f.write(content)

    try:
        df, metadata = parse_file(file_path, filename)
    except ValueError as e:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=str(e))

    dataset_id = generate_dataset_id()
    store_dataset(dataset_id, df, metadata)

    preview = get_preview(df, n=5)

    return UploadResponse(
        success=True,
        dataset_id=dataset_id,
        filename=metadata["filename"],
        file_type=metadata["file_type"],
        file_size_mb=metadata["file_size_mb"],
        rows=metadata["rows"],
        columns=metadata["columns"],
        preview=preview,
    )


@app.post("/api/datasets/analyze", response_model=AnalyzeResponse)
async def analyze_dataset(req: AnalyzeRequest):
    ds = get_dataset(req.dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found or expired.")

    df = ds["dataframe"]
    metadata = ds["metadata"]

    if req.target_column and req.target_column not in df.columns:
        raise HTTPException(
            status_code=400,
            detail=f"Target column '{req.target_column}' not found in dataset.",
        )

    column_profiles = profile_dataset(df)
    data_quality = compute_data_quality(df, column_profiles)
    task_suggestion = suggest_task(df, column_profiles, req.target_column)

    fingerprint = build_fingerprint(
        metadata=metadata,
        df=df,
        column_profiles=column_profiles,
        data_quality=data_quality,
        target_column=req.target_column,
    )

    llm_understanding = call_llm(fingerprint)
    primary = _build_primary_suggestion(task_suggestion, llm_understanding)

    effective_target = req.target_column or primary.target_column or task_suggestion.target_column

    llm_charts = llm_understanding.recommended_charts if llm_understanding else None
    eda_charts = build_eda_charts(df, column_profiles, effective_target, llm_charts)

    preprocessing_previews: list[PreprocessingPreview] = []
    if llm_understanding and llm_understanding.preprocessing_steps:
        preprocessing_previews = generate_preprocessing_previews(df, llm_understanding.preprocessing_steps)

    type_counts = {"numeric": 0, "categorical": 0, "datetime": 0, "boolean": 0, "text": 0, "id_like": 0}
    for p in column_profiles:
        if p.detected_type in type_counts:
            type_counts[p.detected_type] += 1

    overview = Overview(
        rows=metadata["rows"],
        columns=metadata["columns"],
        numeric_columns=type_counts["numeric"],
        categorical_columns=type_counts["categorical"],
        datetime_columns=type_counts["datetime"],
        boolean_columns=type_counts["boolean"],
        text_columns=type_counts["text"],
        id_like_columns=type_counts["id_like"],
        duplicate_rows=data_quality.duplicate_rows,
        total_missing_values=data_quality.total_missing_values,
        suggested_task=primary.suggested_task,
    )

    return AnalyzeResponse(
        success=True,
        dataset_id=req.dataset_id,
        overview=overview,
        preview=get_preview(df, n=5),
        column_profiles=column_profiles,
        data_quality=data_quality,
        eda_charts=eda_charts,
        dataset_fingerprint=fingerprint,
        rule_based_task_suggestion=task_suggestion,
        llm_understanding=llm_understanding,
        primary_task_suggestion=primary,
        preprocessing_previews=preprocessing_previews,
    )


@app.post("/api/llm/dataset-understanding", response_model=LLMResponse)
async def get_llm_understanding(req: LLMRequest):
    ds = get_dataset(req.dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found or expired.")

    understanding = call_llm(req.dataset_fingerprint)

    if understanding:
        return LLMResponse(
            success=True,
            dataset_id=req.dataset_id,
            llm_understanding=understanding,
        )

    return LLMResponse(
        success=False,
        dataset_id=req.dataset_id,
        message="LLM insight unavailable. Basic EDA dashboard is still available.",
    )


@app.post("/api/research/suggestions", response_model=ResearchPRDSuggestionsResponse)
async def research_suggestions(req: ResearchPRDSuggestionsRequest):
    ds = get_dataset(req.dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found or expired.")

    result = get_research_suggestions(req)

    if result:
        titles, tasks, questions = result
        return ResearchPRDSuggestionsResponse(
            success=True,
            dataset_id=req.dataset_id,
            title_suggestions=titles,
            task_suggestions=tasks,
            research_questions=questions,
        )

    return ResearchPRDSuggestionsResponse(
        success=False,
        dataset_id=req.dataset_id,
        title_suggestions=[],
        task_suggestions=[],
        research_questions=[],
    )


@app.post("/api/research/generate-prd", response_model=ResearchPRDResponse)
async def research_generate_prd(req: ResearchPRDRequest):
    ds = get_dataset(req.dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found or expired.")

    prd = generate_research_prd(req)

    if prd:
        return ResearchPRDResponse(
            success=True,
            dataset_id=req.dataset_id,
            prd_markdown=prd,
        )

    return ResearchPRDResponse(
        success=False,
        dataset_id=req.dataset_id,
        prd_markdown="",
    )
