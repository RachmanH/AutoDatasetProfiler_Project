import logging

import numpy as np
import pandas as pd

from models import PreprocessingPreview, PreprocessingStep

logger = logging.getLogger(__name__)


def generate_preprocessing_previews(
    df: pd.DataFrame,
    steps: list[PreprocessingStep],
) -> list[PreprocessingPreview]:
    previews: list[PreprocessingPreview] = []

    for step in steps:
        for col in step.columns:
            if col not in df.columns:
                continue
            try:
                preview = _generate_single_preview(df, step, col)
                if preview:
                    previews.append(preview)
            except Exception as e:
                logger.warning(f"Failed to generate preview for step {step.step_type} on column {col}: {e}")

    return previews


def _generate_single_preview(
    df: pd.DataFrame, step: PreprocessingStep, col: str
) -> PreprocessingPreview | None:
    series = df[col]

    if step.step_type == "handle_missing":
        return _preview_missing(series, col, step.method, step.reason)
    elif step.step_type == "label_encode":
        return _preview_label_encode(series, col, step.method, step.reason)
    elif step.step_type == "one_hot_encode":
        return _preview_one_hot_encode(series, col, step.method, step.reason)
    elif step.step_type == "drop_column":
        return _preview_drop_column(series, col, step.method, step.reason)
    elif step.step_type == "scale":
        return _preview_scale(series, col, step.method, step.reason)
    elif step.step_type == "handle_outlier":
        return _preview_handle_outlier(series, col, step.method, step.reason)

    return None


def _preview_missing(
    series: pd.Series, col: str, method: str, reason: str
) -> PreprocessingPreview | None:
    missing_mask = series.isna()
    missing_count = int(missing_mask.sum())
    if missing_count == 0:
        return None

    before = series[missing_mask].head(5).tolist()
    before = [None if pd.isna(v) else v for v in before]

    non_null = series.dropna()
    fill_value = None
    if "mean" in method.lower():
        fill_value = round(float(non_null.mean()), 2) if pd.api.types.is_numeric_dtype(non_null) else str(non_null.mode().iloc[0]) if len(non_null.mode()) > 0 else None
    elif "median" in method.lower():
        fill_value = round(float(non_null.median()), 2) if pd.api.types.is_numeric_dtype(non_null) else str(non_null.mode().iloc[0]) if len(non_null.mode()) > 0 else None
    elif "mode" in method.lower() or "most_frequent" in method.lower():
        fill_value = str(non_null.mode().iloc[0]) if len(non_null.mode()) > 0 else None
    elif "unknown" in method.lower():
        fill_value = "UNKNOWN"
    else:
        if pd.api.types.is_numeric_dtype(non_null):
            fill_value = round(float(non_null.mean()), 2)
        else:
            fill_value = str(non_null.mode().iloc[0]) if len(non_null.mode()) > 0 else "UNKNOWN"

    after = [fill_value] * min(5, missing_count)

    summary = f"{missing_count} missing values ({round(missing_count / len(series) * 100, 1)}%) would be filled with {fill_value}"

    return PreprocessingPreview(
        step_type="handle_missing",
        column=col,
        method=method,
        reason=reason,
        before_sample=before,
        after_sample=after,
        summary=summary,
    )


def _preview_label_encode(
    series: pd.Series, col: str, method: str, reason: str
) -> PreprocessingPreview | None:
    non_null = series.dropna()
    if non_null.empty:
        return None

    unique_vals = sorted(non_null.unique(), key=str)[:10]
    encoding_map = {str(v): i for i, v in enumerate(unique_vals)}

    before = [str(v) for v in unique_vals[:5]]
    after = [encoding_map[v] for v in before]

    total_unique = non_null.nunique()
    summary = f"{total_unique} unique values would be encoded as integers 0-{total_unique - 1}"
    if total_unique > 10:
        summary += f" (showing first 10 of {total_unique})"

    return PreprocessingPreview(
        step_type="label_encode",
        column=col,
        method=method,
        reason=reason,
        before_sample=before,
        after_sample=after,
        summary=summary,
    )


def _preview_one_hot_encode(
    series: pd.Series, col: str, method: str, reason: str
) -> PreprocessingPreview | None:
    non_null = series.dropna()
    if non_null.empty:
        return None

    unique_vals = non_null.value_counts().head(10)
    total_unique = non_null.nunique()

    before = [str(k) for k in unique_vals.index[:5]]
    after = [f"{col}_{k}" for k in before]

    summary = f"{total_unique} unique values would create {total_unique} new binary columns"
    if total_unique > 10:
        summary += f" (showing top 10 by frequency, full encoding would create {total_unique} columns)"

    return PreprocessingPreview(
        step_type="one_hot_encode",
        column=col,
        method=method,
        reason=reason,
        before_sample=before,
        after_sample=after,
        summary=summary,
    )


def _preview_drop_column(
    series: pd.Series, col: str, method: str, reason: str
) -> PreprocessingPreview | None:
    unique_count = series.nunique()
    missing_count = int(series.isna().sum())
    sample = series.dropna().head(3).tolist()

    before = [str(v) for v in sample]
    after = ["[column removed]"]

    summary = f"Column '{col}' would be removed ({unique_count} unique values, {missing_count} missing)"

    return PreprocessingPreview(
        step_type="drop_column",
        column=col,
        method=method,
        reason=reason,
        before_sample=before,
        after_sample=after,
        summary=summary,
    )


def _preview_scale(
    series: pd.Series, col: str, method: str, reason: str
) -> PreprocessingPreview | None:
    if not pd.api.types.is_numeric_dtype(series):
        return None

    non_null = series.dropna()
    if non_null.empty:
        return None

    before = [round(float(v), 4) for v in non_null.head(5).tolist()]

    if "minmax" in method.lower() or "min_max" in method.lower():
        min_val = float(non_null.min())
        max_val = float(non_null.max())
        range_val = max_val - min_val if max_val != min_val else 1
        after = [round((v - min_val) / range_val, 4) for v in before]
        summary = f"Values scaled to [0, 1] range (min={round(min_val, 2)}, max={round(max_val, 2)})"
    elif "standard" in method.lower() or "zscore" in method.lower() or "z_score" in method.lower():
        mean_val = float(non_null.mean())
        std_val = float(non_null.std()) if float(non_null.std()) > 0 else 1
        after = [round((v - mean_val) / std_val, 4) for v in before]
        summary = f"Values standardized (mean={round(mean_val, 2)}, std={round(std_val, 2)})"
    else:
        mean_val = float(non_null.mean())
        std_val = float(non_null.std()) if float(non_null.std()) > 0 else 1
        after = [round((v - mean_val) / std_val, 4) for v in before]
        summary = f"Values standardized (mean={round(mean_val, 2)}, std={round(std_val, 2)})"

    return PreprocessingPreview(
        step_type="scale",
        column=col,
        method=method,
        reason=reason,
        before_sample=before,
        after_sample=after,
        summary=summary,
    )


def _preview_handle_outlier(
    series: pd.Series, col: str, method: str, reason: str
) -> PreprocessingPreview | None:
    if not pd.api.types.is_numeric_dtype(series):
        return None

    non_null = series.dropna()
    if non_null.empty:
        return None

    q1 = float(non_null.quantile(0.25))
    q3 = float(non_null.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    outlier_mask = (non_null < lower) | (non_null > upper)
    outlier_count = int(outlier_mask.sum())

    if outlier_count == 0:
        return None

    outliers = non_null[outlier_mask].head(5).tolist()
    before = [round(float(v), 4) for v in outliers]

    if "cap" in method.lower() or "clip" in method.lower() or "winsorize" in method.lower():
        after = [round(float(max(lower, min(upper, v))), 4) for v in before]
        summary = f"{outlier_count} outliers ({round(outlier_count / len(non_null) * 100, 1)}%) would be capped to [{round(lower, 2)}, {round(upper, 2)}]"
    else:
        after = [round(float(max(lower, min(upper, v))), 4) for v in before]
        summary = f"{outlier_count} outliers ({round(outlier_count / len(non_null) * 100, 1)}%) would be treated (IQR method)"

    return PreprocessingPreview(
        step_type="handle_outlier",
        column=col,
        method=method,
        reason=reason,
        before_sample=before,
        after_sample=after,
        summary=summary,
    )
