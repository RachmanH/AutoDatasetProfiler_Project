import numpy as np
import pandas as pd

from models import ChartData, ColumnProfile, RecommendedChart


def build_eda_charts(
    df: pd.DataFrame,
    column_profiles: list[ColumnProfile],
    target_column: str | None,
    recommended_charts: list[RecommendedChart] | None = None,
) -> list[ChartData]:
    charts: list[ChartData] = []

    charts.append(_column_type_distribution(column_profiles))

    missing_chart = _missing_value_chart(column_profiles)
    if missing_chart:
        charts.append(missing_chart)

    if recommended_charts:
        dynamic = generate_dynamic_charts(df, recommended_charts, column_profiles)
        charts.extend(dynamic)

        llm_columns: set[str] = set()
        for rc in recommended_charts:
            llm_columns.update(rc.columns)

        target_chart = _target_distribution(df, target_column)
        if target_chart and target_column not in llm_columns:
            charts.append(target_chart)

        numeric_charts = _numeric_distributions(df, column_profiles, target_column, exclude=llm_columns)
        charts.extend(numeric_charts)

        categorical_charts = _categorical_distributions(df, column_profiles, target_column, exclude=llm_columns)
        charts.extend(categorical_charts)
    else:
        target_chart = _target_distribution(df, target_column)
        if target_chart:
            charts.append(target_chart)

        numeric_charts = _numeric_distributions(df, column_profiles, target_column)
        charts.extend(numeric_charts)

        categorical_charts = _categorical_distributions(df, column_profiles, target_column)
        charts.extend(categorical_charts)

    return charts


def generate_charts(
    df: pd.DataFrame,
    column_profiles: list[ColumnProfile],
    target_column: str | None,
) -> list[ChartData]:
    charts: list[ChartData] = []

    charts.append(_column_type_distribution(column_profiles))

    missing_chart = _missing_value_chart(column_profiles)
    if missing_chart:
        charts.append(missing_chart)

    target_chart = _target_distribution(df, target_column)
    if target_chart:
        charts.append(target_chart)

    numeric_charts = _numeric_distributions(df, column_profiles, target_column)
    charts.extend(numeric_charts)

    categorical_charts = _categorical_distributions(df, column_profiles, target_column)
    charts.extend(categorical_charts)

    return charts


def generate_dynamic_charts(
    df: pd.DataFrame,
    recommended_charts: list[RecommendedChart],
    column_profiles: list[ColumnProfile],
) -> list[ChartData]:
    profile_map = {p.column: p for p in column_profiles}
    charts: list[ChartData] = []

    for rec in recommended_charts:
        valid_cols = [c for c in rec.columns if c in df.columns]
        if not valid_cols:
            continue

        try:
            chart = _render_chart(df, rec, profile_map, valid_cols)
            if chart:
                charts.append(chart)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to generate chart '{rec.title}': {e}")

    return charts


def _render_chart(
    df: pd.DataFrame,
    rec: RecommendedChart,
    profile_map: dict,
    valid_cols: list[str],
) -> ChartData | None:
    if rec.chart_type == "bar":
        return _render_bar(df, rec, profile_map, valid_cols)
    elif rec.chart_type == "histogram":
        return _render_histogram(df, rec, profile_map, valid_cols)
    elif rec.chart_type == "pie":
        return _render_pie(df, rec, profile_map, valid_cols)
    elif rec.chart_type == "scatter":
        return _render_scatter(df, rec, profile_map, valid_cols)
    elif rec.chart_type == "boxplot":
        return _render_boxplot(df, rec, profile_map, valid_cols)
    elif rec.chart_type == "grouped_bar":
        return _render_grouped_bar(df, rec, profile_map, valid_cols)
    else:
        return _render_bar(df, rec, profile_map, valid_cols)


def _render_bar(
    df: pd.DataFrame, rec: RecommendedChart, profile_map: dict, valid_cols: list[str]
) -> ChartData | None:
    col = valid_cols[0]
    series = df[col].dropna()
    if series.empty:
        return None
    counts = series.value_counts().head(15)
    data = [{"name": str(k), "count": int(v)} for k, v in counts.items()]
    return ChartData(chart_type="bar", title=rec.title, data=data)


def _render_histogram(
    df: pd.DataFrame, rec: RecommendedChart, profile_map: dict, valid_cols: list[str]
) -> ChartData | None:
    col = valid_cols[0]
    series = df[col].dropna()
    if series.empty or not pd.api.types.is_numeric_dtype(series):
        return None
    n_unique = series.nunique()
    hist, bin_edges = np.histogram(series, bins=min(20, n_unique))
    data = [
        {"name": f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}", "count": int(hist[i])}
        for i in range(len(hist))
    ]
    return ChartData(chart_type="histogram", title=rec.title, data=data)


def _render_pie(
    df: pd.DataFrame, rec: RecommendedChart, profile_map: dict, valid_cols: list[str]
) -> ChartData | None:
    col = valid_cols[0]
    series = df[col].dropna()
    if series.empty:
        return None
    counts = series.value_counts().head(10)
    data = [{"name": str(k), "value": int(v)} for k, v in counts.items()]
    return ChartData(chart_type="pie", title=rec.title, data=data)


def _render_scatter(
    df: pd.DataFrame, rec: RecommendedChart, profile_map: dict, valid_cols: list[str]
) -> ChartData | None:
    if len(valid_cols) < 2:
        col = valid_cols[0]
        if pd.api.types.is_numeric_dtype(df[col]):
            series = df[col].dropna()
            if series.empty:
                return None
            hist, bin_edges = np.histogram(series, bins=min(20, series.nunique()))
            data = [
                {"name": f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}", "count": int(hist[i])}
                for i in range(len(hist))
            ]
            return ChartData(chart_type="histogram", title=rec.title, data=data)
        return None

    x_col, y_col = valid_cols[0], valid_cols[1]
    plot_df = df[[x_col, y_col]].dropna()
    if plot_df.empty:
        return None

    if not pd.api.types.is_numeric_dtype(plot_df[x_col]):
        plot_df[x_col] = plot_df[x_col].astype("category").cat.codes
    if not pd.api.types.is_numeric_dtype(plot_df[y_col]):
        plot_df[y_col] = plot_df[y_col].astype("category").cat.codes

    if len(plot_df) > 500:
        plot_df = plot_df.sample(n=500, random_state=42)

    data = [
        {"x": round(float(row[x_col]), 4), "y": round(float(row[y_col]), 4)}
        for _, row in plot_df.iterrows()
    ]
    return ChartData(chart_type="scatter", title=rec.title, data=data)


def _render_boxplot(
    df: pd.DataFrame, rec: RecommendedChart, profile_map: dict, valid_cols: list[str]
) -> ChartData | None:
    col = valid_cols[0]
    series = df[col].dropna()
    if series.empty or not pd.api.types.is_numeric_dtype(series):
        return None

    q1 = float(series.quantile(0.25))
    q2 = float(series.quantile(0.5))
    q3 = float(series.quantile(0.75))
    iqr = q3 - q1
    lower_whisker = max(float(series.min()), q1 - 1.5 * iqr)
    upper_whisker = min(float(series.max()), q3 + 1.5 * iqr)
    outliers = series[(series < lower_whisker) | (series > upper_whisker)]

    data = [{
        "name": col,
        "min": round(float(series.min()), 4),
        "q1": round(q1, 4),
        "median": round(q2, 4),
        "q3": round(q3, 4),
        "max": round(float(series.max()), 4),
        "lower_whisker": round(lower_whisker, 4),
        "upper_whisker": round(upper_whisker, 4),
        "outlier_count": int(len(outliers)),
    }]
    return ChartData(chart_type="boxplot", title=rec.title, data=data)


def _render_grouped_bar(
    df: pd.DataFrame, rec: RecommendedChart, profile_map: dict, valid_cols: list[str]
) -> ChartData | None:
    if len(valid_cols) < 2:
        return _render_bar(df, rec, profile_map, valid_cols)

    cat_col = valid_cols[0]
    val_col = valid_cols[1]

    cat_profile = profile_map.get(cat_col)
    val_profile = profile_map.get(val_col)

    if val_profile and val_profile.detected_type == "categorical" and cat_profile and cat_profile.detected_type == "categorical":
        ct = pd.crosstab(df[cat_col], df[val_col])
        ct = ct.loc[ct.index.value_counts().head(10).index]
        groups = list(ct.columns)

        data = []
        for idx_name in ct.index:
            row = {"name": str(idx_name)}
            for g in groups:
                row[str(g)] = int(ct.loc[idx_name, g])
            data.append(row)

        return ChartData(chart_type="grouped_bar", title=rec.title, data=data)

    if pd.api.types.is_numeric_dtype(df[val_col]):
        grouped = df.groupby(cat_col, observed=True)[val_col].agg(["mean", "count"])
        grouped = grouped.sort_values("count", ascending=False).head(15)

        data = [
            {"name": str(idx), "mean": round(float(row["mean"]), 2), "count": int(row["count"])}
            for idx, row in grouped.iterrows()
        ]
        return ChartData(chart_type="bar", title=rec.title, data=data)

    return _render_bar(df, rec, profile_map, [cat_col])


def _column_type_distribution(profiles: list[ColumnProfile]) -> ChartData:
    type_counts: dict[str, int] = {}
    for p in profiles:
        t = p.detected_type
        type_counts[t] = type_counts.get(t, 0) + 1

    data = [{"name": k, "value": v} for k, v in sorted(type_counts.items())]
    return ChartData(chart_type="bar", title="Column Type Distribution", data=data)


def _missing_value_chart(profiles: list[ColumnProfile]) -> ChartData | None:
    with_missing = [p for p in profiles if p.missing_count > 0]
    if not with_missing:
        return None

    with_missing.sort(key=lambda p: p.missing_count, reverse=True)
    top10 = with_missing[:10]

    data = [
        {"name": p.column, "missing": p.missing_count, "percentage": p.missing_percentage}
        for p in top10
    ]
    return ChartData(chart_type="horizontal_bar", title="Missing Values (Top 10)", data=data)


def _target_distribution(df: pd.DataFrame, target_column: str | None) -> ChartData | None:
    if not target_column or target_column not in df.columns:
        return None

    series = df[target_column].dropna()

    if pd.api.types.is_numeric_dtype(series) and series.nunique() > 20:
        hist, bin_edges = np.histogram(series, bins=min(20, series.nunique()))
        data = [
            {"name": f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}", "count": int(hist[i])}
            for i in range(len(hist))
        ]
        return ChartData(chart_type="histogram", title=f"Target Distribution: {target_column}", data=data)

    counts = series.value_counts().head(20)
    data = [{"name": str(k), "count": int(v)} for k, v in counts.items()]
    return ChartData(chart_type="bar", title=f"Target Distribution: {target_column}", data=data)


def _numeric_distributions(df: pd.DataFrame, profiles: list[ColumnProfile], target_column: str | None = None, exclude: set[str] | None = None) -> list[ChartData]:
    exclude = exclude or set()
    numeric_cols = [
        p.column for p in profiles
        if p.detected_type == "numeric"
        and p.column in df.columns
        and p.column != target_column
        and p.column not in exclude
    ][:3]

    charts = []
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        hist, bin_edges = np.histogram(series, bins=min(20, series.nunique()))
        data = [
            {"name": f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}", "count": int(hist[i])}
            for i in range(len(hist))
        ]
        charts.append(ChartData(chart_type="histogram", title=f"Distribution: {col}", data=data))

    return charts


def _categorical_distributions(df: pd.DataFrame, profiles: list[ColumnProfile], target_column: str | None = None, exclude: set[str] | None = None) -> list[ChartData]:
    exclude = exclude or set()
    cat_cols = [
        p.column for p in profiles
        if p.detected_type == "categorical"
        and p.column in df.columns
        and p.column != target_column
        and p.column not in exclude
    ][:3]

    charts = []
    for col in cat_cols:
        counts = df[col].value_counts().head(10)
        data = [{"name": str(k), "count": int(v)} for k, v in counts.items()]
        charts.append(ChartData(chart_type="bar", title=f"Distribution: {col}", data=data))

    return charts
