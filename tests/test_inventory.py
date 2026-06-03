from __future__ import annotations

import pandas as pd

from lumina.inventory import inventory_recommendations


def test_inventory_recommendations_flag_stockout():
    sales = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=5, freq="D"),
            "product_id": ["P-1"] * 5,
            "units_sold": [10, 10, 10, 10, 10],
            "net_revenue": [100, 100, 100, 100, 100],
        }
    )
    products = pd.DataFrame(
        {
            "product_id": ["P-1"],
            "product_name": ["Tee"],
            "category": ["Apparel"],
            "supplier": ["Supplier"],
            "current_stock": [5],
            "reorder_point": [10],
            "lead_time_days": [7],
        }
    )

    recommendations = inventory_recommendations(sales, products, lookback_days=5)

    assert bool(recommendations.loc[0, "stockout_risk"]) is True
    assert recommendations.loc[0, "recommended_reorder_qty"] > 0
