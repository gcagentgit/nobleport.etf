"""
OctaStackTrader — Signal Strategy

10/30 EMA crossover with an RSI confirmation filter.

A *buy* fires when the fast EMA crosses above the slow EMA while RSI is below
the overbought threshold (i.e. there's still room to run). A *sell* fires when
the fast EMA crosses below the slow EMA while RSI is above the oversold
threshold. Everything else is ``HOLD``.
"""

from __future__ import annotations

from enum import Enum

from .indicators import ema, rsi


class Signal(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class EmaCrossoverStrategy:
    """EMA-crossover strategy with an RSI filter."""

    def __init__(
        self,
        *,
        fast_ema: int = 10,
        slow_ema: int = 30,
        rsi_period: int = 14,
        rsi_overbought: float = 70.0,
        rsi_oversold: float = 30.0,
    ) -> None:
        if fast_ema >= slow_ema:
            raise ValueError("fast_ema must be < slow_ema")
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold

    @property
    def min_candles(self) -> int:
        """Minimum closes required to evaluate a crossover."""
        return self.slow_ema + 2

    def generate(self, closes: list[float]) -> Signal:
        """Return a :class:`Signal` for the most recent candle in ``closes``."""
        if len(closes) < self.min_candles:
            return Signal.HOLD

        fast = ema(closes, self.fast_ema)
        slow = ema(closes, self.slow_ema)
        rsi_vals = rsi(closes, self.rsi_period)

        f_now, f_prev = fast[-1], fast[-2]
        s_now, s_prev = slow[-1], slow[-2]
        if None in (f_now, f_prev, s_now, s_prev):
            return Signal.HOLD

        # RSI may still be warming up — treat a missing value as neutral (50).
        r = rsi_vals[-1] if rsi_vals[-1] is not None else 50.0

        crossed_up = f_prev <= s_prev and f_now > s_now
        crossed_down = f_prev >= s_prev and f_now < s_now

        if crossed_up and r < self.rsi_overbought:
            return Signal.BUY
        if crossed_down and r > self.rsi_oversold:
            return Signal.SELL
        return Signal.HOLD
