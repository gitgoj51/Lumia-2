"""Configuration constants for Lumina.

All paths are relative to the project root so the application remains portable
and local-first. Lumina never needs credentials, API keys, cloud configuration,
or remote service URLs.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

DEFAULT_FORECAST_HORIZON_DAYS = 30

SALES_REQUIRED_COLUMNS = {
    "date",
    "order_id",
    "product_id",
    "product_name",
    "category",
    "units_sold",
    "unit_price",
    "unit_cost",
    "discount",
    "channel",
}

PRODUCTS_REQUIRED_COLUMNS = {
    "product_id",
    "product_name",
    "category",
    "current_stock",
    "reorder_point",
    "supplier",
    "lead_time_days",
}

EXPENSES_REQUIRED_COLUMNS = {"date", "expense_type", "amount", "notes"}

DATASET_REQUIRED_COLUMNS = {
    "sales": SALES_REQUIRED_COLUMNS,
    "products": PRODUCTS_REQUIRED_COLUMNS,
    "inventory": PRODUCTS_REQUIRED_COLUMNS,
    "expenses": EXPENSES_REQUIRED_COLUMNS,
}
