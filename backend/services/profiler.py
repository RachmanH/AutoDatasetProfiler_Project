import numpy as np
import pandas as pd

from models import ColumnProfile, ColumnStats, DataQuality


def detect_column_type(series: pd.Series, column_name: str, total_rows: int) -> str:
    name_lower = column_name.lower()
    id_patterns = ["id", "uuid", "code", "number", "no", "num", "index", "key"]

    unique_count = series.nunique()
    non_null = series.dropna()

    if any(p in name_lower for p in id_patterns) and unique_count >= total_rows * 0.9:
        return "id_like"

    if unique_count == total_rows and series.dtype in ["int64", "float64"] and non_null.is_monotonic_increasing:
        return "id_like"

    if unique_count == 1:
        return "constant"

    if series.dtype == "bool":
        return "boolean"

    if unique_count == 2:
        vals = set(str(v).lower().strip() for v in non_null.unique())
        boolean_pairs = [
            {"true", "false"}, {"yes", "no"}, {"0", "1"}, {"1", "0"},
            {"t", "f"}, {"y", "n"},
        ]
        if vals in boolean_pairs:
            return "boolean"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    if series.dtype == "object":
        sample = non_null.head(20)
        parsed = pd.to_datetime(sample, errors="coerce", infer_datetime_format=True)
        if parsed.notna().sum() > len(sample) * 0.8:
            return "datetime"

    if pd.api.types.is_numeric_dtype(series):
        if series.dtype in ["float64", "float32"]:
            return "numeric"
        if unique_count > 20:
            return "numeric"
        if unique_count <= 20:
            return "categorical"
        return "numeric"

    if series.dtype == "object":
        avg_len = non_null.astype(str).str.len().mean()
        if avg_len > 50:
            return "text"
        if unique_count > total_rows * 0.5 and unique_count > 50:
            return "text"
        return "categorical"

    return "unknown"


def profile_column(series: pd.Series, column_name: str, total_rows: int) -> ColumnProfile:
    detected_type = detect_column_type(series, column_name, total_rows)
    unique_count = int(series.nunique())
    missing_count = int(series.isnull().sum())
    missing_pct = round((missing_count / total_rows) * 100, 2) if total_rows > 0 else 0.0

    non_null = series.dropna()
    samples = non_null.head(5).tolist()
    samples = [_safe_value(v) for v in samples]

    stats = None
    if pd.api.types.is_numeric_dtype(series):
        stats = ColumnStats(
            mean=round(float(series.mean()), 2) if len(non_null) > 0 else None,
            median=round(float(series.median()), 2) if len(non_null) > 0 else None,
            std=round(float(series.std()), 2) if len(non_null) > 0 else None,
            min=round(float(series.min()), 4) if len(non_null) > 0 else None,
            max=round(float(series.max()), 4) if len(non_null) > 0 else None,
        )

    note = _generate_note(detected_type, missing_pct, unique_count)

    return ColumnProfile(
        column=column_name,
        dtype=str(series.dtype),
        detected_type=detected_type,
        unique_count=unique_count,
        missing_count=missing_count,
        missing_percentage=missing_pct,
        sample_values=samples,
        stats=stats,
        note=note,
    )


def profile_dataset(df: pd.DataFrame) -> list[ColumnProfile]:
    total_rows = len(df)
    profiles = []
    for col in df.columns:
        profiles.append(profile_column(df[col], col, total_rows))
    return profiles


def compute_data_quality(df: pd.DataFrame, profiles: list[ColumnProfile]) -> DataQuality:
    total_missing = int(df.isnull().sum().sum())
    duplicate_rows = int(df.duplicated().sum())
    total_rows = len(df)
    dup_pct = round((duplicate_rows / total_rows) * 100, 2) if total_rows > 0 else 0.0

    id_like = [p.column for p in profiles if p.detected_type == "id_like"]
    constant = [p.column for p in profiles if p.detected_type == "constant"]
    high_card = [
        p.column for p in profiles
        if p.detected_type == "categorical" and p.unique_count > 50
    ]

    return DataQuality(
        total_missing_values=total_missing,
        duplicate_rows=duplicate_rows,
        duplicate_percentage=dup_pct,
        id_like_columns=id_like,
        constant_columns=constant,
        high_cardinality_columns=high_card,
    )


def _safe_value(v):
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return round(float(v), 4)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if pd.isna(v):
        return None
    return v


def _generate_note(detected_type: str, missing_pct: float, unique_count: int) -> str | None:
    notes = []
    if detected_type == "id_like":
        notes.append("ID-like column, likely not useful as a feature")
    if detected_type == "constant":
        notes.append("Constant column with only 1 unique value")
    if missing_pct > 30:
        notes.append(f"High missing rate ({missing_pct}%), consider dropping or special handling")
    elif missing_pct > 5:
        notes.append(f"Moderate missing rate ({missing_pct}%), evaluate before imputation")
    return "; ".join(notes) if notes else None
