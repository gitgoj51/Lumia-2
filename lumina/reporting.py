"""HTML reporting for Lumina."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from lumina.config import OUTPUT_DIR


def generate_html_report(
    metrics: dict[str, float],
    pnl: pd.DataFrame,
    revenue_forecast: pd.DataFrame,
    profit_forecast: pd.DataFrame,
    inventory: pd.DataFrame,
    chart_paths: dict[str, Path],
    sources: dict[str, Path],
    output_path: Path = OUTPUT_DIR / "lumina_report.html",
) -> Path:
    """Generate a standalone local HTML report."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    warnings = _warnings(inventory, metrics)
    chart_links = "".join(
        f"<li><a href='{path.name}'>{name.replace('_', ' ').title()}</a></li>" for name, path in chart_paths.items()
    )
    source_rows = "".join(f"<tr><td>{name}</td><td>{path}</td></tr>" for name, path in sources.items())

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Lumina Retail Analytics Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2933; }}
    h1, h2 {{ color: #102a43; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 8px 10px; text-align: left; }}
    th {{ background: #f0f4f8; }}
    .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; }}
    .metric {{ border: 1px solid #d9e2ec; padding: 12px; }}
    .metric strong {{ display: block; color: #486581; font-size: 13px; }}
    .warning {{ background: #fff8e6; border-left: 4px solid #f0b429; padding: 10px 14px; margin: 8px 0; }}
  </style>
</head>
<body>
  <h1>Lumina Retail Analytics Report</h1>
  <p>Generated locally at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}. No remote assets or external services are used.</p>

  <h2>Financial Summary</h2>
  <div class="metric-grid">
    {_metric_cards(metrics)}
  </div>

  <h2>Warnings</h2>
  {warnings}

  <h2>Profit and Loss</h2>
  {pnl.to_html(index=False)}

  <h2>Forecast Preview</h2>
  <h3>Revenue</h3>
  {revenue_forecast.head(10).to_html(index=False)}
  <h3>Profit</h3>
  {profit_forecast.head(10).to_html(index=False)}

  <h2>Inventory Recommendations</h2>
  {inventory.to_html(index=False)}

  <h2>Charts</h2>
  <ul>{chart_links}</ul>

  <h2>Local Data Sources</h2>
  <table><thead><tr><th>Dataset</th><th>Path</th></tr></thead><tbody>{source_rows}</tbody></table>
</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
    return output_path


def _metric_cards(metrics: dict[str, float]) -> str:
    """Render key metrics as HTML blocks."""

    labels = {
        "gross_revenue": "Gross Revenue",
        "discounts": "Discounts",
        "net_revenue": "Net Revenue",
        "cost_of_goods_sold": "Cost of Goods Sold",
        "gross_profit": "Gross Profit",
        "gross_margin_pct": "Gross Margin %",
        "operating_expenses": "Operating Expenses",
        "net_profit": "Net Profit",
        "profit_margin_pct": "Profit Margin %",
    }
    cards = []
    for key, label in labels.items():
        value = metrics[key]
        rendered = f"{value:,.2f}%" if key.endswith("_pct") else _money(value)
        cards.append(f"<div class='metric'><strong>{label}</strong>{rendered}</div>")
    return "".join(cards)


def _money(value: float) -> str:
    """Render currency with the minus sign before the dollar symbol."""

    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def _warnings(inventory: pd.DataFrame, metrics: dict[str, float]) -> str:
    """Create report warning blocks from financial and inventory signals."""

    messages: list[str] = []
    if metrics["net_profit"] < 0:
        messages.append("Net profit is negative after operating expenses.")
    stockout_count = int(inventory["stockout_risk"].sum())
    overstock_count = int(inventory["overstock_risk"].sum())
    if stockout_count:
        messages.append(f"{stockout_count} product(s) show stockout risk.")
    if overstock_count:
        messages.append(f"{overstock_count} product(s) show overstock risk.")
    if not messages:
        messages.append("No major financial or inventory warnings detected.")
    return "".join(f"<div class='warning'>{message}</div>" for message in messages)
