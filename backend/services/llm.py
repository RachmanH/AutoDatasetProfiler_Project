import json
import logging

import requests

from config import OPENCODE_API_KEY, OPENCODE_MODEL, OPENCODE_URL
from models import DatasetFingerprint, LLMUnderstanding, RecommendedChart, PreprocessingStep

logger = logging.getLogger(__name__)

VALID_TASKS = {
    "binary_classification",
    "multiclass_classification",
    "regression",
    "count_regression",
    "clustering_candidate",
    "unknown",
}

VALID_CONFIDENCES = {"low", "medium", "high"}

VALID_CHART_TYPES = {"bar", "histogram", "pie", "scatter", "boxplot", "grouped_bar"}

VALID_STEP_TYPES = {
    "handle_missing",
    "label_encode",
    "one_hot_encode",
    "drop_column",
    "scale",
    "handle_outlier",
}

SYSTEM_PROMPT = """Kamu adalah asisten EDA untuk dataset tabular.

Gunakan HANYA informasi dari DATASET_FINGERPRINT_JSON.
JANGAN mengarang angka, nama kolom, atau statistik yang tidak tersedia.
Semua nama kolom dalam recommended_charts dan preprocessing_steps HARUS ada di column_names.
Keep all string values SHORT (1-2 sentences max).

Tugasmu:
1. Pahami konteks dataset (1 kalimat).
2. Tebak domain (1-3 kata).
3. Tentukan max 2 kandidat target column.
4. Tentukan task ML yang paling cocok.
5. Rekomendasikan 3-6 chart EDA spesifik dengan nama kolom eksak dan tipe chart.
   - Gunakan tipe: bar, histogram, pie, scatter, boxplot, grouped_bar.
   - Untuk "X_by_Y" atau perbandingan antar kolom, gunakan grouped_bar atau scatter.
   - Untuk distribusi 1 kolom numerik, gunakan histogram.
   - Untuk distribusi 1 kolom kategorikal, gunakan bar.
   - Untuk outlier detection kolom numerik, gunakan boxplot.
6. Rekomendasikan 2-5 langkah preprocessing spesifik dengan nama kolom eksak dan metode.
   - Gunakan step_type: handle_missing, label_encode, one_hot_encode, drop_column, scale, handle_outlier.
   - Untuk kolom kategorikal yang akan jadi feature: label_encode (ordinal) atau one_hot_encode (nominal, unique < 20).
   - Untuk kolom dengan missing value: handle_missing dengan metode mean/median/mode/unknown_category.
   - Untuk kolom ID-like atau constant: drop_column.
   - Untuk outlier: handle_outlier dengan metode cap/winsorize.
7. Berikan max 3 warning metodologis.
8. Tentukan hal yang perlu dikonfirmasi user.

Keluarkan JSON valid saja, tanpa markdown.

Output JSON schema:
{
  "dataset_understanding": "string (1 kalimat)",
  "domain_guess": "string (1-3 kata)",
  "target_candidates": [
    {"column": "string", "reason": "string", "confidence": "low|medium|high"}
  ],
  "suggested_task": "binary_classification|multiclass_classification|regression|count_regression|clustering_candidate|unknown",
  "task_reason": "string",
  "recommended_eda": ["string (deskripsi singkat)"],
  "recommended_charts": [
    {
      "chart_type": "bar|histogram|pie|scatter|boxplot|grouped_bar",
      "title": "string (judul chart)",
      "columns": ["col1", "col2"],
      "reason": "string (mengapa chart ini penting)"
    }
  ],
  "preprocessing_recommendations": ["string (deskripsi singkat)"],
  "preprocessing_steps": [
    {
      "step_type": "handle_missing|label_encode|one_hot_encode|drop_column|scale|handle_outlier",
      "columns": ["col1"],
      "method": "string (metode spesifik, misal: mean_imputation, label_encoding)",
      "reason": "string"
    }
  ],
  "methodological_warnings": ["string"],
  "user_confirmation_needed": ["string"]
}"""


def call_llm(fingerprint: DatasetFingerprint) -> LLMUnderstanding | None:
    if not OPENCODE_API_KEY:
        logger.warning("OPENCODE_API_KEY not set, skipping LLM call")
        return None

    fingerprint_json = fingerprint.model_dump()

    user_prompt = f"DATASET_FINGERPRINT_JSON:\n{json.dumps(fingerprint_json, indent=2, default=str)}"

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
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0,
                "max_tokens": 8192,
            },
            timeout=120,
        )
        response.raise_for_status()

        result = response.json()
        message = result["choices"][0]["message"]
        content = message.get("content", "")

        if not content or not content.strip():
            content = message.get("reasoning_content", "")
            logger.warning("LLM content was empty, using reasoning_content as fallback")

        logger.info(f"LLM response content (first 200 chars): {content[:200]}")

        return _parse_and_validate(content, fingerprint)

    except requests.RequestException as e:
        logger.error(f"LLM API request failed: {e}")
        return None
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error(f"Failed to parse LLM response: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected LLM error: {type(e).__name__}: {e}")
        return None


def _try_parse_json(raw: str) -> dict | None:
    # Strategy 1: direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Strategy 2: extract JSON object
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass

    # Strategy 3: repair truncated JSON
    if start != -1:
        text = raw[start:]
        # Try progressively closing from the end, removing incomplete entries
        for trim in range(min(200, len(text)), 0, -1):
            candidate = text[:len(text) - trim] if trim < len(text) else text
            # Remove trailing comma, whitespace, incomplete strings
            candidate = candidate.rstrip()
            if candidate.endswith('"') or candidate.endswith(','):
                candidate = candidate[:candidate.rfind(',') if ',' in candidate else len(candidate)]
                candidate = candidate.rstrip().rstrip(',')
            # Count and close open brackets
            opens = []
            in_string = False
            escape = False
            for ch in candidate:
                if escape:
                    escape = False
                    continue
                if ch == '\\':
                    escape = True
                    continue
                if ch == '"':
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch in ('{', '['):
                    opens.append(ch)
                elif ch in ('}', ']'):
                    if opens:
                        opens.pop()
            # Close remaining open brackets
            for bracket in reversed(opens):
                candidate += ']' if bracket == '[' else '}'
            try:
                result = json.loads(candidate)
                if isinstance(result, dict):
                    logger.info(f"Successfully repaired truncated JSON (trimmed {trim} chars)")
                    return result
            except json.JSONDecodeError:
                continue

    return None


def _parse_and_validate(raw: str, fingerprint: DatasetFingerprint) -> LLMUnderstanding | None:
    logger.info(f"Raw LLM content length: {len(raw)} chars")

    data = _try_parse_json(raw)

    if data is None:
        logger.error("All JSON parsing attempts failed")
        logger.error(f"Content (first 500 chars):\n{raw[:500]}")
        return None

    if data.get("suggested_task") not in VALID_TASKS:
        data["suggested_task"] = "unknown"

    # Fill defaults for required fields that may be missing in truncated responses
    data.setdefault("dataset_understanding", "")
    data.setdefault("domain_guess", "")
    data.setdefault("target_candidates", [])
    data.setdefault("task_reason", "")
    data.setdefault("recommended_eda", [])
    data.setdefault("recommended_charts", [])
    data.setdefault("preprocessing_recommendations", [])
    data.setdefault("preprocessing_steps", [])
    data.setdefault("methodological_warnings", [])
    data.setdefault("user_confirmation_needed", [])

    valid_columns = set(fingerprint.column_names)

    if "target_candidates" in data:
        data["target_candidates"] = [
            tc for tc in data["target_candidates"]
            if isinstance(tc, dict)
            and tc.get("column") in valid_columns
            and tc.get("confidence") in VALID_CONFIDENCES
        ]

    if "recommended_charts" in data:
        validated_charts = []
        for rc in data["recommended_charts"]:
            if not isinstance(rc, dict):
                continue
            cols = rc.get("columns", [])
            if not all(c in valid_columns for c in cols):
                logger.warning(f"Skipping chart with invalid columns: {cols}")
                continue
            if rc.get("chart_type") not in VALID_CHART_TYPES:
                rc["chart_type"] = "bar"
            validated_charts.append(rc)
        data["recommended_charts"] = validated_charts

    if "preprocessing_steps" in data:
        validated_steps = []
        for ps in data["preprocessing_steps"]:
            if not isinstance(ps, dict):
                continue
            cols = ps.get("columns", [])
            if not all(c in valid_columns for c in cols):
                logger.warning(f"Skipping preprocessing step with invalid columns: {cols}")
                continue
            if ps.get("step_type") not in VALID_STEP_TYPES:
                logger.warning(f"Skipping step with invalid step_type: {ps.get('step_type')}")
                continue
            validated_steps.append(ps)
        data["preprocessing_steps"] = validated_steps

    # ensure backward compat fields exist
    if "recommended_eda" not in data:
        data["recommended_eda"] = []
    if "preprocessing_recommendations" not in data:
        data["preprocessing_recommendations"] = []

    try:
        return LLMUnderstanding(**data)
    except Exception as e:
        logger.error(f"LLM output validation failed: {e}")
        return None
