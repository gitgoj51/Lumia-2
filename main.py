"""Lumina demonstration CLI."""

from __future__ import annotations

from pathlib import Path

from lumina.analytics import (
    calculate_financial_metrics,
    profit_and_loss_summary,
    revenue_by_category,
    revenue_by_channel,
    revenue_by_product,
    sales_trends,
)
from lumina.config import DATA_DIR, DEFAULT_FORECAST_HORIZON_DAYS
from lumina.forecasting import forecast_profit, forecast_revenue
from lumina.ingestion import load_dataset
from lumina.inventory import inventory_recommendations
from lumina.reporting import generate_html_report
from lumina.security import enforce_local_first
from lumina.visualization import generate_all_charts


def main() -> None:
    """Run the sample Lumina analytics pipeline."""

    sources = {
        "sales": DATA_DIR / "sample_sales.csv",
        "products": DATA_DIR / "sample_products.csv",
        "expenses": DATA_DIR / "sample_expenses.csv",
    }

    with enforce_local_first():
        sales = load_dataset(sources["sales"], "sales")
        products = load_dataset(sources["products"], "products")
        expenses = load_dataset(sources["expenses"], "expenses")

        metrics = calculate_financial_metrics(sales, expenses)
        daily = sales_trends(sales, "D")
        category = revenue_by_category(sales)
        products_revenue = revenue_by_product(sales)
        channel = revenue_by_channel(sales)
        pnl = profit_and_loss_summary(sales, expenses)

        revenue_forecast = forecast_revenue(daily, DEFAULT_FORECAST_HORIZON_DAYS)
        profit_forecast = forecast_profit(daily, DEFAULT_FORECAST_HORIZON_DAYS)
        inventory = inventory_recommendations(sales, products)

        chart_paths = generate_all_charts(
            daily,
            category,
            products_revenue,
            inventory,
            revenue_forecast.frame,
            profit_forecast.frame,
        )
        report_path = generate_html_report(
            metrics,
            pnl,
            revenue_forecast.frame,
            profit_forecast.frame,
            inventory,
            chart_paths,
            {key: Path(value) for key, value in sources.items()},
        )

    print("Lumina local retail analytics complete")
    print(f"Net revenue: {_money(metrics['net_revenue'])}")
    print(f"Net profit: {_money(metrics['net_profit'])}")
    print(f"Gross margin: {metrics['gross_margin_pct']:.2f}%")
    print(f"Top channel: {channel.sort_values('net_revenue', ascending=False).iloc[0]['channel']}")
    print(f"Stockout risks: {int(inventory['stockout_risk'].sum())}")
    print(f"Report: {report_path}")


def _money(value: float) -> str:
    """Render currency with the minus sign before the dollar symbol."""

    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


if __name__ == "__main__":
    main()
