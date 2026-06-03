"""Financial analytics for local retail datasets."""

from __future__ import annotations

import pandas as pd


def calculate_financial_metrics(sales: pd.DataFrame, expenses: pd.DataFrame) -> dict[str, float]:
    """Calculate high-level retail financial metrics."""

    gross_revenue = float(sales["gross_revenue"].sum())
    discounts = float(sales["discount"].sum())
    net_revenue = float(sales["net_revenue"].sum())
    cogs = float(sales["cogs"].sum())
    gross_profit = float(sales["gross_profit"].sum())
    operating_expenses = float(expenses["amount"].sum())
    net_profit = gross_profit - operating_expenses
    gross_margin_pct = _ratio(gross_profit, net_revenue) * 100
    profit_margin_pct = _ratio(net_profit, net_revenue) * 100

    return {
        "gross_revenue": gross_revenue,
        "discounts": discounts,
        "net_revenue": net_revenue,
        "cost_of_goods_sold": cogs,
        "gross_profit": gross_profit,
        "gross_margin_pct": gross_margin_pct,
        "operating_expenses": operating_expenses,
        "net_profit": net_profit,
        "profit_margin_pct": profit_margin_pct,
    }


def revenue_by_product(sales: pd.DataFrame) -> pd.DataFrame:
    """Return net revenue and units sold by product."""

    return _group_sales(sales, ["product_id", "product_name"]).sort_values("net_revenue", ascending=False)


def revenue_by_category(sales: pd.DataFrame) -> pd.DataFrame:
    """Return net revenue and units sold by category."""

    return _group_sales(sales, ["category"]).sort_values("net_revenue", ascending=False)


def revenue_by_channel(sales: pd.DataFrame) -> pd.DataFrame:
    """Return net revenue and units sold by sales channel."""

    return _group_sales(sales, ["channel"]).sort_values("net_revenue", ascending=False)


def sales_trends(sales: pd.DataFrame, frequency: str = "D") -> pd.DataFrame:
    """Return sales trends for daily, weekly, or monthly periods."""

    trend = (
        sales.set_index("date")
        .resample(frequency)
        .agg(
            gross_revenue=("gross_revenue", "sum"),
            net_revenue=("net_revenue", "sum"),
            cogs=("cogs", "sum"),
            gross_profit=("gross_profit", "sum"),
            units_sold=("units_sold", "sum"),
        )
        .reset_index()
    )
    return trend


def best_selling_products(sales: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    """Return products with the highest units sold."""

    return _group_sales(sales, ["product_id", "product_name"]).sort_values("units_sold", ascending=False).head(limit)


def worst_selling_products(sales: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    """Return products with the lowest units sold."""

    return _group_sales(sales, ["product_id", "product_name"]).sort_values("units_sold", ascending=True).head(limit)


def profit_and_loss_summary(sales: pd.DataFrame, expenses: pd.DataFrame) -> pd.DataFrame:
    """Build a profit-and-loss summary table."""

    metrics = calculate_financial_metrics(sales, expenses)
    rows = [
        ("Gross revenue", metrics["gross_revenue"]),
        ("Discounts", -metrics["discounts"]),
        ("Net revenue", metrics["net_revenue"]),
        ("Cost of goods sold", -metrics["cost_of_goods_sold"]),
        ("Gross profit", metrics["gross_profit"]),
        ("Operating expenses", -metrics["operating_expenses"]),
        ("Net profit", metrics["net_profit"]),
    ]
    return pd.DataFrame(rows, columns=["line_item", "amount"])


def _group_sales(sales: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Aggregate common sales measures by a dimension list."""

    return (
        sales.groupby(keys, as_index=False)
        .agg(
            units_sold=("units_sold", "sum"),
            gross_revenue=("gross_revenue", "sum"),
            net_revenue=("net_revenue", "sum"),
            gross_profit=("gross_profit", "sum"),
        )
        .round(2)
    )


def _ratio(numerator: float, denominator: float) -> float:
    """Return a safe ratio."""

    return 0.0 if denominator == 0 else numerator / denominator
