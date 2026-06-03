"""Inventory optimization and reorder recommendations."""

from __future__ import annotations

import numpy as np
import pandas as pd


def inventory_recommendations(
    sales: pd.DataFrame,
    products: pd.DataFrame,
    lookback_days: int = 30,
    safety_stock_days: int = 7,
) -> pd.DataFrame:
    """Create product-level inventory recommendations.

    Sales velocity is calculated from recent local sales. Reorder quantities
    cover supplier lead time plus safety stock, adjusted by current inventory.
    """

    if lookback_days < 1:
        raise ValueError("lookback_days must be positive.")

    latest_date = pd.to_datetime(sales["date"]).max()
    cutoff = latest_date - pd.Timedelta(days=lookback_days - 1)
    recent = sales[pd.to_datetime(sales["date"]) >= cutoff]

    velocity = (
        recent.groupby("product_id", as_index=False)
        .agg(units_sold=("units_sold", "sum"), revenue=("net_revenue", "sum"))
        .assign(sales_velocity_per_day=lambda frame: frame["units_sold"] / lookback_days)
    )

    merged = products.merge(velocity, on="product_id", how="left").fillna(
        {"units_sold": 0, "revenue": 0.0, "sales_velocity_per_day": 0.0}
    )
    velocity_values = merged["sales_velocity_per_day"].replace(0, np.nan)
    merged["days_of_stock_remaining"] = (merged["current_stock"] / velocity_values).replace([np.inf, -np.inf], np.nan)
    merged["days_of_stock_remaining"] = merged["days_of_stock_remaining"].fillna(9999).round(1)
    merged["target_stock"] = np.ceil(
        merged["sales_velocity_per_day"] * (merged["lead_time_days"] + safety_stock_days)
    ).astype(int)
    merged["recommended_reorder_qty"] = (merged["target_stock"] - merged["current_stock"]).clip(lower=0).astype(int)
    merged["stockout_risk"] = (
        (merged["current_stock"] <= merged["reorder_point"])
        | (merged["days_of_stock_remaining"] <= merged["lead_time_days"] + safety_stock_days)
    )
    merged["overstock_risk"] = (
        (merged["days_of_stock_remaining"] > 90)
        & (merged["current_stock"] > merged["reorder_point"] * 2)
    )

    fast_threshold = merged["sales_velocity_per_day"].quantile(0.75)
    slow_threshold = merged["sales_velocity_per_day"].quantile(0.25)
    merged["movement_class"] = np.select(
        [
            merged["sales_velocity_per_day"] >= fast_threshold,
            merged["sales_velocity_per_day"] <= slow_threshold,
        ],
        ["fast-moving", "slow-moving"],
        default="normal",
    )

    merged["recommendation"] = np.select(
        [
            merged["stockout_risk"],
            merged["overstock_risk"],
            merged["movement_class"] == "slow-moving",
        ],
        [
            "Reorder or expedite supplier follow-up",
            "Reduce purchasing and consider promotion",
            "Monitor demand before replenishing",
        ],
        default="Maintain current replenishment cadence",
    )

    columns = [
        "product_id",
        "product_name",
        "category",
        "supplier",
        "current_stock",
        "reorder_point",
        "lead_time_days",
        "sales_velocity_per_day",
        "days_of_stock_remaining",
        "recommended_reorder_qty",
        "movement_class",
        "stockout_risk",
        "overstock_risk",
        "recommendation",
    ]
    return merged[columns].sort_values(["stockout_risk", "recommended_reorder_qty"], ascending=[False, False])
