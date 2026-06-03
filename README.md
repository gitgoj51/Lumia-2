# Lumina: Local-First Retail Analytics Engine

Lumina is a self-contained Python analytics project for retail operators who want business intelligence without sending data to a cloud service. It ingests local CSV or JSON files, validates and normalizes them, calculates financial metrics, forecasts revenue and profit, recommends inventory actions, creates local charts, and generates an HTML report.

## Why Local-First

Lumina only reads and writes local files. It does not call external APIs, require API keys, upload data, use telemetry, or depend on hosted dashboards. The optional runtime guard in `lumina/security.py` blocks common Python socket usage while the pipeline runs.

## Features

- CSV and JSON ingestion for sales, products/inventory, and expenses
- Schema validation with helpful malformed-data errors
- Net revenue, gross revenue, discounts, COGS, gross profit, margin, operating expenses, net profit, and P&L summary
- Revenue by product, category, and channel
- Daily, weekly, and monthly trend calculations
- Revenue and profit forecasting with statsmodels Exponential Smoothing and a local regression fallback
- Inventory velocity, days of stock remaining, reorder quantities, slow/fast mover detection, stockout risk, and overstock risk
- Offline-safe Plotly HTML charts with Matplotlib PNG fallback
- Standalone local HTML report in `outputs/lumina_report.html`

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS or Linux, activate with:

```bash
source .venv/bin/activate
```

## Usage

```bash
python main.py
```

The command creates:

- `outputs/lumina_report.html`
- `outputs/revenue_forecast.html`
- `outputs/profit_forecast.html`
- `outputs/inventory_risk.html`
- `outputs/revenue_trends.html`

Run tests with:

```bash
pytest
```

## Data Schema

Sales columns:

`date`, `order_id`, `product_id`, `product_name`, `category`, `units_sold`, `unit_price`, `unit_cost`, `discount`, `channel`

Products/inventory columns:

`product_id`, `product_name`, `category`, `current_stock`, `reorder_point`, `supplier`, `lead_time_days`

Expenses columns:

`date`, `expense_type`, `amount`, `notes`

## Security Guarantees

- No external network calls are required or intentionally made.
- No API keys, secrets, credentials, trackers, telemetry, or cloud URLs are used.
- URL-like dataset paths are rejected.
- Reports and charts are written to the local `outputs/` directory.
- Plotly charts are written with local embedded JavaScript instead of a remote CDN.

## Future Improvements

- Add per-store and per-region dimensions.
- Add seasonality diagnostics and model comparison reports.
- Support configurable service-level targets for inventory planning.
- Export report tables to Excel.
- Add a CLI for custom file paths and forecast horizons.
