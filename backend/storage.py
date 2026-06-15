import time
import uuid
from typing import Optional

import pandas as pd

from config import DATASET_TTL_SECONDS

_datasets: dict[str, dict] = {}


def generate_dataset_id() -> str:
    return f"ds_{uuid.uuid4().hex[:12]}"


def store_dataset(dataset_id: str, dataframe: pd.DataFrame, metadata: dict) -> None:
    _datasets[dataset_id] = {
        "dataframe": dataframe,
        "metadata": metadata,
        "created_at": time.time(),
    }
    _cleanup_expired()


def get_dataset(dataset_id: str) -> Optional[dict]:
    _cleanup_expired()
    return _datasets.get(dataset_id)


def delete_dataset(dataset_id: str) -> None:
    _datasets.pop(dataset_id, None)


def _cleanup_expired() -> None:
    now = time.time()
    expired = [
        did for did, ds in _datasets.items()
        if now - ds["created_at"] > DATASET_TTL_SECONDS
    ]
    for did in expired:
        del _datasets[did]
