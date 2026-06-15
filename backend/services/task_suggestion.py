import pandas as pd

from models import ColumnProfile, RuleBasedTaskSuggestion


def suggest_task(
    df: pd.DataFrame,
    column_profiles: list[ColumnProfile],
    target_column: str | None,
) -> RuleBasedTaskSuggestion:
    if target_column and target_column in df.columns:
        series = df[target_column]
        profile = next((p for p in column_profiles if p.column == target_column), None)

        unique_count = series.nunique()
        is_numeric = pd.api.types.is_numeric_dtype(series)
        detected = profile.detected_type if profile else None

        if not is_numeric or detected in ("categorical", "boolean"):
            if unique_count == 2:
                return RuleBasedTaskSuggestion(
                    suggested_task="binary_classification",
                    reason=f"Target '{target_column}' has exactly 2 unique values.",
                    target_column=target_column,
                )
            else:
                return RuleBasedTaskSuggestion(
                    suggested_task="multiclass_classification",
                    reason=f"Target '{target_column}' is categorical with {unique_count} unique values.",
                    target_column=target_column,
                )

        if is_numeric:
            non_null = series.dropna()
            is_integer = pd.api.types.is_integer_dtype(series)

            if is_integer and non_null.min() >= 0 and unique_count <= 30:
                return RuleBasedTaskSuggestion(
                    suggested_task="count_regression",
                    reason=f"Target '{target_column}' is non-negative integer with {unique_count} unique values, typical of count data.",
                    target_column=target_column,
                )

            return RuleBasedTaskSuggestion(
                suggested_task="regression",
                reason=f"Target '{target_column}' is a continuous numeric column with {unique_count} unique values.",
                target_column=target_column,
            )

    candidates = _find_candidate_targets(df, column_profiles)

    if candidates:
        col, reason = candidates[0]
        series = df[col]
        unique_count = series.nunique()
        is_numeric = pd.api.types.is_numeric_dtype(series)

        if not is_numeric or unique_count <= 20:
            task = "binary_classification" if unique_count == 2 else "multiclass_classification"
        else:
            task = "regression"

        return RuleBasedTaskSuggestion(
            suggested_task=task,
            reason=reason,
            target_column=col,
        )

    return RuleBasedTaskSuggestion(
        suggested_task="clustering_candidate",
        reason="No clear target column detected. Dataset may be suitable for unsupervised clustering.",
        target_column=None,
    )


def _find_candidate_targets(
    df: pd.DataFrame, profiles: list[ColumnProfile]
) -> list[tuple[str, str]]:
    candidates = []
    target_keywords = ["target", "label", "class", "result", "outcome", "status", "survived", "price", "sale", "score"]

    for profile in profiles:
        name_lower = profile.column.lower()
        if any(kw in name_lower for kw in target_keywords):
            if profile.detected_type not in ("id_like", "constant"):
                candidates.append((
                    profile.column,
                    f"Column '{profile.column}' name suggests it could be a target variable.",
                ))

    for profile in profiles:
        if profile.column in [c[0] for c in candidates]:
            continue
        if profile.detected_type == "boolean":
            candidates.append((
                profile.column,
                f"Column '{profile.column}' is boolean with 2 values, a common target pattern.",
            ))
        elif profile.detected_type == "categorical" and profile.unique_count <= 10:
            candidates.append((
                profile.column,
                f"Column '{profile.column}' is categorical with {profile.unique_count} classes.",
            ))

    return candidates
