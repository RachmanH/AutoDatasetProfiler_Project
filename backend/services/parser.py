import os
import re

import pandas as pd


def parse_file(file_path: str, filename: str) -> tuple[pd.DataFrame, dict]:
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".csv":
        df = pd.read_csv(file_path)
        file_type = "csv"
    elif ext == ".xlsx":
        df = pd.read_excel(file_path, engine="openpyxl", sheet_name=0)
        file_type = "xlsx"
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    if df.empty:
        raise ValueError("Dataset is empty or unreadable.")

    if len(df.columns) == 0:
        raise ValueError("Dataset has no columns.")

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    metadata = {
        "filename": _sanitize_filename(filename),
        "file_type": file_type,
        "file_size_mb": round(file_size_mb, 4),
        "rows": len(df),
        "columns": len(df.columns),
    }

    return df, metadata


def get_preview(df: pd.DataFrame, n: int = 5) -> list[dict]:
    preview_df = df.head(n).copy()
    preview_df = preview_df.where(pd.notnull(preview_df), None)
    return preview_df.to_dict(orient="records")


def _sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    filename = re.sub(r"[^\w\-.]", "_", filename)
    return filename
