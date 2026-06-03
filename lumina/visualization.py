"""Offline-safe chart generation for Lumina."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from lumina.config import OUTPUT_DIR


def generate_all_charts(
    daily_trend: pd.DataFrame,
    category_revenue: pd.DataFrame,
    product_revenue: pd.DataFrame,
    inventory: pd.DataFrame,
    revenue_forecast: pd.DataFrame,
    profit_forecast: pd.DataFrame,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, Path]:
    """Generate all standard charts and return their local paths."""

    output_dir.mkdir(parents=True, exist_ok=True)
    return {
        "revenue_trends": revenue_over_time(daily_trend, output_dir / "revenue_trends.html"),
        "profit_trends": profit_over_time(daily_trend, output_dir / "profit_trends.html"),
        "sales_by_category": sales_by_category(category_revenue, output_dir / "sales_by_category.html"),
        "top_products": top_products(product_revenue, output_dir / "top_products.html"),
        "inventory_risk": inventory_risk(inventory, output_dir / "inventory_risk.html"),
        "revenue_forecast": forecast_chart(revenue_forecast, "Revenue Forecast", output_dir / "revenue_forecast.html"),
        "profit_forecast": forecast_chart(profit_forecast, "Profit Forecast", output_dir / "profit_forecast.html"),
    }


def revenue_over_time(trend: pd.DataFrame, path: Path) -> Path:
    """Save a revenue-over-time chart."""

    return _plot_line(trend, "date", ["net_revenue", "gross_revenue"], "Revenue Over Time", path)


def profit_over_time(trend: pd.DataFrame, path: Path) -> Path:
    """Save a profit-over-time chart."""

    return _plot_line(trend, "date", ["gross_profit"], "Profit Over Time", path)


def sales_by_category(category_revenue: pd.DataFrame, path: Path) -> Path:
    """Save a category revenue bar chart."""

    return _plot_bar(category_revenue, "category", "net_revenue", "Sales by Category", path)


def top_products(product_revenue: pd.DataFrame, path: Path, limit: int = 10) -> Path:
    """Save a top-products revenue chart."""

    top = product_revenue.head(limit).copy()
    return _plot_bar(top, "product_name", "net_revenue", "Top Products", path)


def inventory_risk(inventory: pd.DataFrame, path: Path) -> Path:
    """Save an inventory risk chart."""

    risk = inventory.copy()
    risk["risk_score"] = risk["stockout_risk"].astype(int) * 2 + risk["overstock_risk"].astype(int)
    return _plot_bar(risk, "product_name", "risk_score", "Inventory Risk", path)


def forecast_chart(forecast: pd.DataFrame, title: str, path: Path) -> Path:
    """Save a forecast chart with confidence-style bands."""

    try:
        import plotly.graph_objects as go

        figure = go.Figure()
        figure.add_trace(go.Scatter(x=forecast["date"], y=forecast["forecast"], name="forecast", mode="lines"))
        figure.add_trace(
            go.Scatter(
                x=list(forecast["date"]) + list(forecast["date"])[::-1],
                y=list(forecast["upper"]) + list(forecast["lower"])[::-1],
                fill="toself",
                fillcolor="rgba(50, 120, 200, 0.18)",
                line={"color": "rgba(255,255,255,0)"},
                name="confidence band",
            )
        )
        figure.update_layout(title=title, template="plotly_white")
        figure.write_html(path, include_plotlyjs=True, full_html=True)
    except Exception:
        _matplotlib_line(forecast, "date", ["forecast", "lower", "upper"], title, path.with_suffix(".png"))
        return path.with_suffix(".png")
    return path


def _plot_line(frame: pd.DataFrame, x: str, y_columns: list[str], title: str, path: Path) -> Path:
    """Save a line chart with Plotly, falling back to Matplotlib."""

    try:
        import plotly.express as px

        figure = px.line(frame, x=x, y=y_columns, title=title)
        figure.update_layout(template="plotly_white")
        figure.write_html(path, include_plotlyjs=True, full_html=True)
    except Exception:
        _matplotlib_line(frame, x, y_columns, title, path.with_suffix(".png"))
        return path.with_suffix(".png")
    return path


def _plot_bar(frame: pd.DataFrame, x: str, y: str, title: str, path: Path) -> Path:
    """Save a bar chart with Plotly, falling back to Matplotlib."""

    try:
        import plotly.express as px

        figure = px.bar(frame, x=x, y=y, title=title)
        figure.update_layout(template="plotly_white")
        figure.write_html(path, include_plotlyjs=True, full_html=True)
    except Exception:
        import matplotlib.pyplot as plt

        png_path = path.with_suffix(".png")
        ax = frame.plot(kind="bar", x=x, y=y, title=title, legend=False)
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        plt.tight_layout()
        plt.savefig(png_path)
        plt.close()
        return png_path
    return path


def _matplotlib_line(frame: pd.DataFrame, x: str, y_columns: list[str], title: str, path: Path) -> None:
    """Save a line chart using Matplotlib."""

    import matplotlib.pyplot as plt

    ax = frame.plot(x=x, y=y_columns, title=title)
    ax.set_xlabel(x)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
