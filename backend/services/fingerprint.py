from models import (
    ColumnProfile,
    DataQuality,
    DatasetFingerprint,
    DatasetMetadata,
)
from services.parser import get_preview

import pandas as pd


def build_fingerprint(
    metadata: dict,
    df: pd.DataFrame,
    column_profiles: list[ColumnProfile],
    data_quality: DataQuality,
    target_column: str | None = None,
) -> DatasetFingerprint:
    return DatasetFingerprint(
        metadata=DatasetMetadata(**metadata),
        column_names=list(df.columns),
        preview_rows=get_preview(df, n=5),
        column_profiles=column_profiles,
        data_quality=data_quality,
        target_column_selected_by_user=target_column,
    )
