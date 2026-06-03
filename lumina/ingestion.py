"""Local CSV and JSON ingestion for Lumina."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import pandas as pd

from lumina.security import assert_local_path
from lumina.validation import require_non_negative, validate_required_columns

DatasetType = Literal["sales", "products", "inventory", "expenses"]


def load_dataset(path: str | Path, dataset_type: DatasetType) -> pd.DataFrame:
    """Load and normalize a supported local dataset.

    CSV and JSON files are read from local disk only. JSON may be either a list
    of objects or a records-style pandas JSON document.
    """

    local_path = assert_local_path(path)
    if not local_path.exists():
        raise FileNotFoundError(f"Dataset not found: {local_path}")

    suffix = local_path.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(local_path)
    elif suffix == ".json":
        frame = _read_json(local_path)
    else:
        raise ValueError("Unsupported file type. Use CSV or JSON.")

    validate_required_columns(frame, dataset_type)
    return normalize_dataset(frame, dataset_type)


def normalize_dataset(frame: pd.DataFrame, dataset_type: DatasetType) -> pd.DataFrame:
    """Normalize date, identifier, text, and numeric fields for a dataset."""

    normalized = frame.copy()
    normalized.columns = [str(column).strip() for column in normalized.columns]

    if dataset_type == "sales":
        normalized["date"] = _parse_dates(normalized["date"], dataset_type)
        for column in ["units_sold", "unit_price", "unit_cost", "discount"]:
            normalized[column] = _number(normalized[column], column, dataset_type)
        require_non_negative(normalized, ["units_sold", "unit_price", "unit_cost", "discount"], dataset_type)
        normalized["discount"] = normalized["discount"].fillna(0.0)
        normalized["units_sold"] = normalized["units_sold"].round().astype(int)
        normalized["gross_revenue"] = normalized["units_sold"] * normalized["unit_price"]
        normalized["net_revenue"] = (normalized["gross_revenue"] - normalized["discount"]).clip(lower=0)
        normalized["cogs"] = normalized["units_sold"] * normalized["unit_cost"]
        normalized["gross_profit"] = normalized["net_revenue"] - normalized["cogs"]
        text_columns = ["order_id", "product_id", "product_name", "category", "channel"]
    elif dataset_type in {"products", "inventory"}:
        for column in ["current_stock", "reorder_point", "lead_time_days"]:
            normalized[column] = _number(normalized[column], column, dataset_type)
        require_non_negative(normalized, ["current_stock", "reorder_point", "lead_time_days"], dataset_type)
        normalized["current_stock"] = normalized["current_stock"].round().astype(int)
        normalized["reorder_point"] = normalized["reorder_point"].round().astype(int)
        normalized["lead_time_days"] = normalized["lead_time_days"].round().astype(int)
        text_columns = ["product_id", "product_name", "category", "supplier"]
    elif dataset_type == "expenses":
        normalized["date"] = _parse_dates(normalized["date"], dataset_type)
        normalized["amount"] = _number(normalized["amount"], "amount", dataset_type)
        require_non_negative(normalized, ["amount"], dataset_type)
        text_columns = ["expense_type", "notes"]
    else:
        raise ValueError(f"Unknown dataset type '{dataset_type}'.")

    for column in text_columns:
        normalized[column] = normalized[column].fillna("Unknown").astype(str).str.strip()
        if (normalized[column] == "").any():
            normalized.loc[normalized[column] == "", column] = "Unknown"

    return normalized


def _read_json(path: Path) -> pd.DataFrame:
    """Read a local JSON dataset with helpful malformed-data errors."""

    try:
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON in {path}: {exc}") from exc

    if isinstance(raw, list):
        return pd.DataFrame(raw)
    if isinstance(raw, dict):
        return pd.DataFrame(raw.get("records", raw))
    raise ValueError("JSON dataset must be a list of records or an object containing records.")


def _parse_dates(series: pd.Series, dataset_type: str) -> pd.Series:
    """Parse dates and reject invalid date values."""

    parsed = pd.to_datetime(series, errors="coerce")
    if parsed.isna().any():
        raise ValueError(f"{dataset_type}.date contains invalid dates.")
    return parsed.dt.normalize()


def _number(series: pd.Series, column: str, dataset_type: str) -> pd.Series:
    """Parse numeric values and reject invalid values."""

    parsed = pd.to_numeric(series, errors="coerce")
    if parsed.isna().any():
        raise ValueError(f"{dataset_type}.{column} contains missing or non-numeric values.")
    return parsed.astype(float)
