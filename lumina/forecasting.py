"""Local forecasting engine for revenue and profit."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ForecastResult:
    """Forecast output with confidence-style bands."""

    metric: str
    model_name: str
    frame: pd.DataFrame


def forecast_metric(
    series: pd.DataFrame,
    value_column: str,
    horizon_days: int = 30,
    metric_name: str | None = None,
) -> ForecastResult:
    """Forecast a daily metric using local time-series models.

    Lumina first attempts statsmodels Exponential Smoothing because it handles
    trend and seasonality well for retail series. If statsmodels is unavailable
    or the data is too short, it falls back to a deterministic regression model
    with rolling-residual bands. No remote services are used.
    """

    metric = metric_name or value_column
    daily = _prepare_daily_series(series, value_column)
    if horizon_days < 1:
        raise ValueError("Forecast horizon must be at least 1 day.")

    try:
        return _statsmodels_forecast(daily, horizon_days, metric)
    except Exception:
        return _regression_forecast(daily, horizon_days, metric)


def forecast_revenue(sales_trend: pd.DataFrame, horizon_days: int = 30) -> ForecastResult:
    """Forecast future net revenue."""

    return forecast_metric(sales_trend, "net_revenue", horizon_days, "revenue")


def forecast_profit(sales_trend: pd.DataFrame, horizon_days: int = 30) -> ForecastResult:
    """Forecast future gross profit."""

    return forecast_metric(sales_trend, "gross_profit", horizon_days, "profit")


def _prepare_daily_series(frame: pd.DataFrame, value_column: str) -> pd.Series:
    """Prepare a complete daily time series for forecasting."""

    if "date" not in frame.columns or value_column not in frame.columns:
        raise ValueError(f"Forecast input must include date and {value_column}.")

    daily = frame[["date", value_column]].copy()
    daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
    if daily["date"].isna().any():
        raise ValueError("Forecast input contains invalid dates.")

    series = daily.set_index("date")[value_column].astype(float).sort_index().asfreq("D")
    return series.interpolate(limit_direction="both").fillna(0.0)


def _statsmodels_forecast(series: pd.Series, horizon_days: int, metric: str) -> ForecastResult:
    """Forecast with statsmodels Exponential Smoothing when available."""

    if len(series) < 14:
        raise ValueError("At least 14 daily observations are needed for exponential smoothing.")

    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    seasonal_periods = 7 if len(series) >= 21 else None
    model = ExponentialSmoothing(
        series,
        trend="add",
        seasonal="add" if seasonal_periods else None,
        seasonal_periods=seasonal_periods,
        initialization_method="estimated",
    )
    fitted = model.fit(optimized=True)
    forecast = fitted.forecast(horizon_days)
    residual_std = float(np.nanstd(fitted.resid)) or float(series.std()) or 1.0
    output = _format_forecast(series.index[-1], forecast.to_numpy(), residual_std)
    return ForecastResult(metric=metric, model_name="ExponentialSmoothing", frame=output)


def _regression_forecast(series: pd.Series, horizon_days: int, metric: str) -> ForecastResult:
    """Forecast with a deterministic linear trend fallback."""

    x = np.arange(len(series), dtype=float)
    y = series.to_numpy(dtype=float)
    if len(series) == 1:
        slope, intercept = 0.0, y[0]
        fitted = np.repeat(y[0], len(y))
    else:
        slope, intercept = np.polyfit(x, y, 1)
        fitted = slope * x + intercept
    future_x = np.arange(len(series), len(series) + horizon_days, dtype=float)
    forecast = slope * future_x + intercept
    residual_std = float(np.nanstd(y - fitted)) or float(np.nanstd(y)) or 1.0
    output = _format_forecast(series.index[-1], forecast, residual_std)
    return ForecastResult(metric=metric, model_name="LinearRegressionFallback", frame=output)


def _format_forecast(last_date: pd.Timestamp, forecast: np.ndarray, residual_std: float) -> pd.DataFrame:
    """Format forecast values with lower and upper bands."""

    dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=len(forecast), freq="D")
    values = np.maximum(forecast, 0.0)
    spread = 1.96 * residual_std
    return pd.DataFrame(
        {
            "date": dates,
            "forecast": values.round(2),
            "lower": np.maximum(values - spread, 0.0).round(2),
            "upper": (values + spread).round(2),
        }
    )
