"""Validation helpers for local retail datasets."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from lumina.config import DATASET_REQUIRED_COLUMNS


@dataclass(frozen=True)
class ValidationResult:
    """Result object returned by dataset validation."""

    dataset_type: str
    row_count: int
    columns: list[str]


def validate_required_columns(frame: pd.DataFrame, dataset_type: str) -> ValidationResult:
    """Validate that a dataframe has the expected columns for a dataset type."""

    if dataset_type not in DATASET_REQUIRED_COLUMNS:
        raise ValueError(f"Unknown dataset type '{dataset_type}'.")

    required = DATASET_REQUIRED_COLUMNS[dataset_type]
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{dataset_type} data is missing required columns: {', '.join(missing)}")

    if frame.empty:
        raise ValueError(f"{dataset_type} data is empty.")

    return ValidationResult(dataset_type=dataset_type, row_count=len(frame), columns=list(frame.columns))


def require_non_negative(frame: pd.DataFrame, columns: list[str], dataset_type: str) -> None:
    """Reject negative numeric values in the supplied columns."""

    for column in columns:
        if column in frame.columns and (frame[column] < 0).any():
            raise ValueError(f"{dataset_type}.{column} contains negative values.")
