from __future__ import annotations

import pandas as pd

from lumina.forecasting import forecast_revenue


def test_forecast_generation_returns_horizon():
    trend = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=10, freq="D"),
            "net_revenue": [100 + index * 5 for index in range(10)],
        }
    )

    result = forecast_revenue(trend, horizon_days=7)

    assert len(result.frame) == 7
    assert {"date", "forecast", "lower", "upper"}.issubset(result.frame.columns)
    assert (result.frame["forecast"] >= 0).all()
