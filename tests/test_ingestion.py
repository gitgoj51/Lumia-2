from __future__ import annotations

import pandas as pd
import pytest

from lumina.ingestion import load_dataset


def test_load_sales_csv_normalizes_financial_columns(tmp_path):
    path = tmp_path / "sales.csv"
    path.write_text(
        "date,order_id,product_id,product_name,category,units_sold,unit_price,unit_cost,discount,channel\n"
        "2026-01-01,O-1,P-1,Tee,Apparel,2,10,4,1,Store\n",
        encoding="utf-8",
    )

    frame = load_dataset(path, "sales")

    assert frame.loc[0, "net_revenue"] == 19
    assert frame.loc[0, "gross_profit"] == 11
    assert pd.api.types.is_datetime64_any_dtype(frame["date"])


def test_bad_input_missing_required_columns(tmp_path):
    path = tmp_path / "sales.csv"
    path.write_text("date,order_id\n2026-01-01,O-1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required columns"):
        load_dataset(path, "sales")
