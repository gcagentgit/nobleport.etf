"""
OctaStackTrader — Technical Indicators

Pure-Python indicator implementations so the strategy core has no hard
dependency on pandas/numpy and can run (and be unit-tested) anywhere.
Each function takes a list of closing prices and returns a list aligned to
the input, with ``None`` for leading positions that have insufficient data.
"""

from __future__ import annotations


def ema(values: list[float], period: int) -> list[float | None]:
    """
    Exponential Moving Average.

    Seeded with a simple moving average over the first ``period`` values, then
    smoothed with ``alpha = 2 / (period + 1)``. Positions before the seed are
    ``None``.
    """
    if period <= 0:
        raise ValueError("period must be > 0")
    n = len(values)
    out: list[float | None] = [None] * n
    if n < period:
        return out

    alpha = 2.0 / (period + 1.0)
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    prev = seed
    for i in range(period, n):
        prev = (values[i] - prev) * alpha + prev
        out[i] = prev
    return out


def rsi(values: list[float], period: int) -> list[float | None]:
    """
    Relative Strength Index using Wilder's smoothing.

    Returns values in ``[0, 100]``; leading positions without enough data are
    ``None``. A zero average-loss yields an RSI of 100 (pure uptrend).
    """
    if period <= 0:
        raise ValueError("period must be > 0")
    n = len(values)
    out: list[float | None] = [None] * n
    if n <= period:
        return out

    gains = 0.0
    losses = 0.0
    for i in range(1, period + 1):
        delta = values[i] - values[i - 1]
        if delta >= 0:
            gains += delta
        else:
            losses -= delta
    avg_gain = gains / period
    avg_loss = losses / period
    out[period] = _rsi_from_avgs(avg_gain, avg_loss)

    for i in range(period + 1, n):
        delta = values[i] - values[i - 1]
        gain = delta if delta > 0 else 0.0
        loss = -delta if delta < 0 else 0.0
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        out[i] = _rsi_from_avgs(avg_gain, avg_loss)
    return out


def _rsi_from_avgs(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))
