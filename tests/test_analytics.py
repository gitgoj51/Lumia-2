from __future__ import annotations

import pandas as pd

from lumina.analytics import calculate_financial_metrics, profit_and_loss_summary


def test_financial_calculations():
    sales = pd.DataFrame(
        {
            "gross_revenue": [100.0, 200.0],
            "discount": [10.0, 0.0],
            "net_revenue": [90.0, 200.0],
            "cogs": [40.0, 80.0],
            "gross_profit": [50.0, 120.0],
        }
    )
    expenses = pd.DataFrame({"amount": [50.0]})

    metrics = calculate_financial_metrics(sales, expenses)

    assert metrics["net_revenue"] == 290.0
    assert metrics["gross_profit"] == 170.0
    assert metrics["net_profit"] == 120.0
    assert round(metrics["profit_margin_pct"], 2) == 41.38


def test_pnl_summary_contains_net_profit():
    sales = pd.DataFrame(
        {"gross_revenue": [50.0], "discount": [0.0], "net_revenue": [50.0], "cogs": [20.0], "gross_profit": [30.0]}
    )
    expenses = pd.DataFrame({"amount": [10.0]})

    pnl = profit_and_loss_summary(sales, expenses)

    assert "Net profit" in pnl["line_item"].tolist()
    assert pnl.loc[pnl["line_item"] == "Net profit", "amount"].iloc[0] == 20.0
