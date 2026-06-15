from pydantic import BaseModel
from typing import Optional


class UploadResponse(BaseModel):
    success: bool
    dataset_id: str
    filename: str
    file_type: str
    file_size_mb: float
    rows: int
    columns: int
    preview: list[dict]


class AnalyzeRequest(BaseModel):
    dataset_id: str
    target_column: Optional[str] = None


class ColumnStats(BaseModel):
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None


class ColumnProfile(BaseModel):
    column: str
    dtype: str
    detected_type: str
    unique_count: int
    missing_count: int
    missing_percentage: float
    sample_values: list
    stats: Optional[ColumnStats] = None
    note: Optional[str] = None


class DataQuality(BaseModel):
    total_missing_values: int
    duplicate_rows: int
    duplicate_percentage: float
    id_like_columns: list[str]
    constant_columns: list[str]
    high_cardinality_columns: list[str]


class DatasetMetadata(BaseModel):
    filename: str
    file_type: str
    file_size_mb: float
    rows: int
    columns: int


class DatasetFingerprint(BaseModel):
    metadata: DatasetMetadata
    column_names: list[str]
    preview_rows: list[dict]
    column_profiles: list[ColumnProfile]
    data_quality: DataQuality
    target_column_selected_by_user: Optional[str] = None


class Overview(BaseModel):
    rows: int
    columns: int
    numeric_columns: int
    categorical_columns: int
    datetime_columns: int
    boolean_columns: int
    text_columns: int
    id_like_columns: int
    duplicate_rows: int
    total_missing_values: int
    suggested_task: str


class RuleBasedTaskSuggestion(BaseModel):
    suggested_task: str
    reason: str
    target_column: Optional[str] = None


class PrimaryTaskSuggestion(BaseModel):
    suggested_task: str
    reason: str
    target_column: Optional[str] = None
    source: str  # "llm" or "rule_based"
    confidence: Optional[str] = None
    target_candidates: Optional[list[dict]] = None
    domain_guess: Optional[str] = None


class ChartData(BaseModel):
    chart_type: str
    title: str
    data: list[dict]


class AnalyzeResponse(BaseModel):
    success: bool
    dataset_id: str
    overview: Overview
    preview: list[dict]
    column_profiles: list[ColumnProfile]
    data_quality: DataQuality
    eda_charts: list[ChartData]
    dataset_fingerprint: DatasetFingerprint
    rule_based_task_suggestion: RuleBasedTaskSuggestion
    llm_understanding: Optional["LLMUnderstanding"] = None
    primary_task_suggestion: PrimaryTaskSuggestion
    preprocessing_previews: list["PreprocessingPreview"] = []


class RecommendedChart(BaseModel):
    chart_type: str  # bar, histogram, pie, scatter, boxplot, grouped_bar
    title: str
    columns: list[str]  # nama kolom yang terlibat
    reason: str


class PreprocessingStep(BaseModel):
    step_type: str  # handle_missing, label_encode, one_hot_encode, drop_column, scale, handle_outlier
    columns: list[str]
    method: str  # metode spesifik, misal: "mean_imputation", "median_imputation", "label_encoding"
    reason: str


class PreprocessingPreview(BaseModel):
    step_type: str
    column: str
    method: str
    reason: str
    before_sample: list
    after_sample: list
    summary: str


class TargetCandidate(BaseModel):
    column: str
    reason: str
    confidence: str


class LLMUnderstanding(BaseModel):
    dataset_understanding: str
    domain_guess: str
    target_candidates: list[TargetCandidate]
    suggested_task: str
    task_reason: str
    recommended_eda: list[str]  # backward compat
    recommended_charts: list[RecommendedChart] = []  # structured chart specs
    preprocessing_recommendations: list[str]  # backward compat (text)
    preprocessing_steps: list[PreprocessingStep] = []  # structured preprocessing
    methodological_warnings: list[str]
    user_confirmation_needed: list[str]


class LLMRequest(BaseModel):
    dataset_id: str
    dataset_fingerprint: DatasetFingerprint


class LLMResponse(BaseModel):
    success: bool
    dataset_id: str
    llm_understanding: Optional[LLMUnderstanding] = None
    message: Optional[str] = None

AnalyzeResponse.model_rebuild()


class ResearchTitleSuggestion(BaseModel):
    title: str
    description: str
    task: str  # binary_classification, multiclass_classification, regression, etc.
    method_suggestion: str  # suggested ML method or approach


class ResearchTaskSuggestion(BaseModel):
    task: str
    description: str
    suitable_methods: list[str]
    evaluation_metrics: list[str]


class ResearchPRDSuggestionsRequest(BaseModel):
    dataset_id: str
    dataset_fingerprint: DatasetFingerprint
    llm_understanding: Optional["LLMUnderstanding"] = None
    primary_task_suggestion: Optional[PrimaryTaskSuggestion] = None


class ResearchPRDSuggestionsResponse(BaseModel):
    success: bool
    dataset_id: str
    title_suggestions: list[ResearchTitleSuggestion]
    task_suggestions: list[ResearchTaskSuggestion]
    research_questions: list[str]


class ResearchPRDRequest(BaseModel):
    dataset_id: str
    selected_title: str
    selected_task: str
    research_background: str
    research_objectives: list[str]
    research_questions: list[str]
    target_column: Optional[str] = None
    additional_notes: Optional[str] = None
    dataset_fingerprint: DatasetFingerprint
    llm_understanding: Optional["LLMUnderstanding"] = None


class ResearchPRDResponse(BaseModel):
    success: bool
    dataset_id: str
    prd_markdown: str

ResearchPRDSuggestionsResponse.model_rebuild()
ResearchPRDResponse.model_rebuild()

