import json
import logging

import requests

from config import OPENCODE_API_KEY, OPENCODE_MODEL, OPENCODE_URL
from models import (
    DatasetFingerprint,
    LLMUnderstanding,
    PrimaryTaskSuggestion,
    ResearchPRDRequest,
    ResearchPRDSuggestionsRequest,
    ResearchTaskSuggestion,
    ResearchTitleSuggestion,
)

logger = logging.getLogger(__name__)

VALID_TASKS = {
    "binary_classification",
    "multiclass_classification",
    "regression",
    "count_regression",
    "clustering_candidate",
    "unknown",
}

SUGGESTIONS_PROMPT = """Kamu adalah asisten riset machine learning untuk mahasiswa.

Berdasarkan DATASET_FINGERPRINT_JSON dan ANALYSIS_RESULT di bawah, berikan saran untuk PRD riset.

Tugasmu:
1. Berikan 3 pilihan JUDUL RISET yang spesifik, akademis, dan sesuai dataset.
   - Setiap judul harus mencakup: nama domain, task ML, dan pendekatan.
   - Gunakan bahasa Indonesia formal akademis.
   - Sertakan task ML yang sesuai dan metode yang direkomendasikan.

2. Berikan 2-3 saran TASK RISET dengan detail:
   - Nama task (binary_classification, multiclass_classification, regression, dll)
   - Deskripsi singkat mengapa task ini cocok
   - Metode ML yang cocok (min 3 metode per task)
   - Metrik evaluasi yang sesuai

3. Berikan 3-5 RESEARCH QUESTIONS (pertanyaan riset) yang bisa dijawab dengan dataset ini.
   - Gunakan bahasa Indonesia.
   - Pertanyaan harus spesifik dan dapat diuji secara empiris.

Keluarkan JSON valid saja, tanpa markdown.

Output JSON schema:
{
  "title_suggestions": [
    {
      "title": "string (judul riset dalam bahasa Indonesia)",
      "description": "string (deskripsi singkat 1-2 kalimat)",
      "task": "binary_classification|multiclass_classification|regression|count_regression|clustering_candidate",
      "method_suggestion": "string (metode ML yang direkomendasikan)"
    }
  ],
  "task_suggestions": [
    {
      "task": "string",
      "description": "string (alasan mengapa task ini cocok)",
      "suitable_methods": ["method1", "method2", "method3"],
      "evaluation_metrics": ["metric1", "metric2"]
    }
  ],
  "research_questions": [
    "string (pertanyaan riset dalam bahasa Indonesia)"
  ]
}"""


PRD_PROMPT = """Kamu adalah asisten penulisan PRD (Product Requirements Document) riset machine learning untuk mahasiswa.

Berdasarkan informasi berikut:
- DATASET_FINGERPRINT_JSON: ringkasan dataset
- ANALYSIS_RESULT: hasil analisis dataset
- USER_INPUT: pilihan dan input user

Tugasmu: buat PRD riset lengkap dalam format Markdown yang siap digunakan untuk skripsi/tugas akhir.

Struktur PRD yang harus dibuat:

# PRD Riset: {judul}

## 1. Latar Belakang
- Konteks domain dan masalah
- Mengapa dataset ini relevan
- Gap yang ingin diisi

## 2. Rumusan Masalah
- Daftar pertanyaan riset dari user input

## 3. Tujuan Riset
- Daftar tujuan dari user input

## 4. Dataset
- Deskripsi dataset (nama, ukuran, kolom)
- Kolom target dan fitur
- Karakteristik data (missing value, imbalance, dll)

## 5. Task Machine Learning
- Task yang dipilih dan alasannya
- Definisi input dan output model

## 6. Metodologi
### 6.1 Preprocessing
- Langkah preprocessing berdasarkan analisis
### 6.2 Model yang Akan Diuji
- Daftar model dan alasan pemilihan
### 6.3 Metrik Evaluasi
- Metrik yang digunakan dan alasannya
### 6.4 Skema Validasi
- Cross-validation strategy

## 7. Eksperimen
- Rencana eksperimen
- Baseline model
- Perbandingan model

## 8. Risiko dan Mitigasi
- Risiko potensial dan cara mitigasi

## 9. Timeline (Estimasi)
- Estimasi waktu per tahap

## 10. Referensi Awal
- Saran paper/referensi yang relevan

Gunakan bahasa Indonesia akademis formal.
Jangan mengarang data yang tidak ada di fingerprint.
Output hanya Markdown, tanpa pembungkus JSON."""


def get_research_suggestions(
    req: ResearchPRDSuggestionsRequest,
) -> tuple[list[ResearchTitleSuggestion], list[ResearchTaskSuggestion], list[str]] | None:
    if not OPENCODE_API_KEY:
        logger.warning("OPENCODE_API_KEY not set")
        return None

    context = {
        "fingerprint": req.dataset_fingerprint.model_dump(),
    }
    if req.llm_understanding:
        context["llm_analysis"] = {
            "domain_guess": req.llm_understanding.domain_guess,
            "suggested_task": req.llm_understanding.suggested_task,
            "target_candidates": [
                {"column": tc.column, "reason": tc.reason}
                for tc in req.llm_understanding.target_candidates
            ],
        }
    if req.primary_task_suggestion:
        context["primary_suggestion"] = {
            "task": req.primary_task_suggestion.suggested_task,
            "target": req.primary_task_suggestion.target_column,
            "reason": req.primary_task_suggestion.reason,
        }

    user_prompt = f"DATASET_FINGERPRINT_JSON dan ANALYSIS_RESULT:\n{json.dumps(context, indent=2, default=str)}"

    try:
        response = requests.post(
            OPENCODE_URL,
            headers={
                "Authorization": f"Bearer {OPENCODE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENCODE_MODEL,
                "messages": [
                    {"role": "system", "content": SUGGESTIONS_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 4096,
            },
            timeout=120,
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"].get("content", "")
        if not content.strip():
            content = result["choices"][0]["message"].get("reasoning_content", "")

        data = _extract_json(content)
        if not data:
            return None

        valid_columns = set(req.dataset_fingerprint.column_names)

        titles = []
        for t in data.get("title_suggestions", []):
            if isinstance(t, dict) and t.get("title"):
                if t.get("task") not in VALID_TASKS:
                    t["task"] = req.primary_task_suggestion.suggested_task if req.primary_task_suggestion else "unknown"
                titles.append(ResearchTitleSuggestion(**t))

        tasks = []
        for ts in data.get("task_suggestions", []):
            if isinstance(ts, dict) and ts.get("task"):
                if ts.get("task") not in VALID_TASKS:
                    continue
                tasks.append(ResearchTaskSuggestion(**ts))

        questions = [q for q in data.get("research_questions", []) if isinstance(q, str)]

        return titles, tasks, questions

    except Exception as e:
        logger.error(f"Research suggestions failed: {type(e).__name__}: {e}")
        return None


def generate_research_prd(req: ResearchPRDRequest) -> str | None:
    if not OPENCODE_API_KEY:
        logger.warning("OPENCODE_API_KEY not set")
        return None

    context = {
        "fingerprint": req.dataset_fingerprint.model_dump(),
        "user_input": {
            "selected_title": req.selected_title,
            "selected_task": req.selected_task,
            "research_background": req.research_background,
            "research_objectives": req.research_objectives,
            "research_questions": req.research_questions,
            "target_column": req.target_column,
            "additional_notes": req.additional_notes,
        },
    }
    if req.llm_understanding:
        context["llm_analysis"] = {
            "domain_guess": req.llm_understanding.domain_guess,
            "suggested_task": req.llm_understanding.suggested_task,
            "preprocessing_recommendations": req.llm_understanding.preprocessing_recommendations,
            "methodological_warnings": req.llm_understanding.methodological_warnings,
        }

    user_prompt = f"DATASET_FINGERPRINT_JSON, ANALYSIS_RESULT, dan USER_INPUT:\n{json.dumps(context, indent=2, default=str)}"

    try:
        response = requests.post(
            OPENCODE_URL,
            headers={
                "Authorization": f"Bearer {OPENCODE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENCODE_MODEL,
                "messages": [
                    {"role": "system", "content": PRD_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.5,
                "max_tokens": 8192,
            },
            timeout=180,
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"].get("content", "")
        if not content.strip():
            content = result["choices"][0]["message"].get("reasoning_content", "")

        return content.strip() if content.strip() else None

    except Exception as e:
        logger.error(f"Research PRD generation failed: {type(e).__name__}: {e}")
        return None


def _extract_json(raw: str) -> dict | None:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass
    return None
