"""
OctaStackTrader — unit tests.

These run with zero third-party dependencies (no ccxt / pandas), using a stub
market-data feed and the in-memory paper broker.
"""

from __future__ import annotations

import math

from backend.trading.bot import OctaStackTrader
from backend.trading.broker import MarketData, PaperBroker
from backend.trading.config import TradingConfig
from backend.trading.indicators import ema, rsi
from backend.trading.risk import position_size, stop_loss_price, take_profit_price
from backend.trading.strategy import EmaCrossoverStrategy, Signal


# --------------------------------------------------------------------------- #
# Stubs
# --------------------------------------------------------------------------- #
class StubMarketData(MarketData):
    def __init__(self, closes: list[float], price: float | None = None) -> None:
        self.closes = closes
        self.price = price if price is not None else closes[-1]

    def fetch_closes(self, symbol, timeframe, limit):
        return self.closes

    def fetch_price(self, symbol):
        return self.price


class StubStrategy:
    """Always emits a fixed signal — decouples engine tests from indicators."""

    def __init__(self, signal: Signal) -> None:
        self.signal = signal
        self.min_candles = 1

    def generate(self, closes):
        return self.signal


def _cfg(**overrides) -> TradingConfig:
    base = dict(
        symbols=["BTC/USDT"],
        max_positions=8,
        risk_per_trade=0.02,
        stop_loss_pct=0.05,
        take_profit_tiers=[(0.05, 0.5), (0.10, 1.0)],
        order_size_min=10.0,
        starting_paper_balance=1_000_000.0,
        log_file="",  # disable CSV writes in tests
    )
    base.update(overrides)
    cfg = TradingConfig(**base)
    cfg.validate()
    return cfg


def _engine(cfg, market, strategy=None) -> OctaStackTrader:
    broker = PaperBroker(
        quote_currency=cfg.quote_currency,
        starting_balance=cfg.starting_paper_balance,
    )
    return OctaStackTrader(cfg, market, broker, strategy=strategy)


# --------------------------------------------------------------------------- #
# Indicators
# --------------------------------------------------------------------------- #
def test_ema_constant_series_is_constant():
    out = ema([100.0] * 20, period=5)
    assert out[:4] == [None, None, None, None]
    assert all(abs(v - 100.0) < 1e-9 for v in out[4:])


def test_rsi_monotonic_increasing_is_100():
    out = rsi([float(i) for i in range(1, 30)], period=14)
    assert out[14] is not None
    assert abs(out[-1] - 100.0) < 1e-9


def test_rsi_within_bounds():
    series = [10, 11, 10.5, 12, 11.5, 13, 12, 14, 13, 15, 14, 16, 15, 17, 16, 18]
    for v in rsi([float(x) for x in series], period=5):
        if v is not None:
            assert 0.0 <= v <= 100.0


# --------------------------------------------------------------------------- #
# Strategy
# --------------------------------------------------------------------------- #
def test_strategy_buy_on_bullish_crossover():
    strat = EmaCrossoverStrategy(
        fast_ema=3, slow_ema=5, rsi_period=3,
        rsi_overbought=200.0, rsi_oversold=-1.0,
    )
    # Decline then a sharp rebound forces the fast EMA above the slow EMA
    # exactly on the final bar.
    closes = [10, 9, 8, 7, 6, 5, 6, 8, 11]
    assert strat.generate([float(c) for c in closes]) is Signal.BUY


def test_strategy_sell_on_bearish_crossover():
    strat = EmaCrossoverStrategy(
        fast_ema=3, slow_ema=5, rsi_period=3,
        rsi_overbought=200.0, rsi_oversold=-1.0,
    )
    closes = [5, 6, 7, 8, 9, 10, 9, 7, 4]
    assert strat.generate([float(c) for c in closes]) is Signal.SELL


def test_strategy_holds_without_enough_data():
    strat = EmaCrossoverStrategy(fast_ema=10, slow_ema=30)
    assert strat.generate([1.0, 2.0, 3.0]) is Signal.HOLD


# --------------------------------------------------------------------------- #
# Risk
# --------------------------------------------------------------------------- #
def test_position_size_matches_risk_math():
    qty = position_size(
        price=100.0, balance=10_000.0, risk_per_trade=0.02,
        stop_loss_pct=0.05, order_size_min=10.0,
    )
    # risk 200 / stop distance 5 = 40 units
    assert abs(qty - 40.0) < 1e-9


def test_position_size_respects_min_notional():
    qty = position_size(
        price=100.0, balance=10.0, risk_per_trade=0.02,
        stop_loss_pct=0.05, order_size_min=10.0,
    )
    assert qty * 100.0 >= 10.0 - 1e-9


def test_stop_and_take_profit_prices():
    assert math.isclose(stop_loss_price(100.0, 0.05), 95.0)
    assert math.isclose(take_profit_price(100.0, 0.10), 110.0)


# --------------------------------------------------------------------------- #
# Paper broker
# --------------------------------------------------------------------------- #
def test_paper_broker_buy_then_sell_updates_balances():
    pb = PaperBroker(quote_currency="USDT", starting_balance=1_000.0)
    assert pb.market_buy("BTC/USDT", 2.0, 100.0)  # spend 200
    assert math.isclose(pb.free_balance("USDT"), 800.0)
    assert math.isclose(pb.free_balance("BTC"), 2.0)
    assert pb.market_sell("BTC/USDT", 2.0, 150.0)  # gain 300
    assert math.isclose(pb.free_balance("USDT"), 1_100.0)
    assert math.isclose(pb.free_balance("BTC"), 0.0)


def test_paper_broker_rejects_overspend():
    pb = PaperBroker(quote_currency="USDT", starting_balance=50.0)
    assert pb.market_buy("BTC/USDT", 1.0, 100.0) is False


# --------------------------------------------------------------------------- #
# Engine
# --------------------------------------------------------------------------- #
def test_engine_enforces_eight_position_stack():
    symbols = [f"C{i}/USDT" for i in range(12)]
    cfg = _cfg(symbols=symbols, max_positions=8)
    market = StubMarketData(closes=[100.0] * 5, price=100.0)
    eng = _engine(cfg, market, strategy=StubStrategy(Signal.BUY))
    eng.step()
    assert len(eng.positions) == 8


def test_engine_take_profit_ladder():
    cfg = _cfg()
    market = StubMarketData(closes=[100.0] * 5, price=100.0)
    eng = _engine(cfg, market, strategy=StubStrategy(Signal.HOLD))
    assert eng.open_position("BTC/USDT", 100.0)
    pos = eng.positions["BTC/USDT"]
    initial = pos.initial_quantity

    # +6% → first tier (+5%) books half.
    market.price = 106.0
    eng.check_exits()
    assert "BTC/USDT" in eng.positions
    assert math.isclose(eng.positions["BTC/USDT"].quantity, initial * 0.5)

    # +11% → second tier (+10%) books the rest and closes the position.
    market.price = 111.0
    eng.check_exits()
    assert "BTC/USDT" not in eng.positions


def test_engine_stop_loss_exit():
    cfg = _cfg()
    market = StubMarketData(closes=[100.0] * 5, price=100.0)
    eng = _engine(cfg, market, strategy=StubStrategy(Signal.HOLD))
    eng.open_position("BTC/USDT", 100.0)
    market.price = 94.0  # below the 95.0 stop
    eng.check_exits()
    assert "BTC/USDT" not in eng.positions


def test_engine_sell_signal_closes_position():
    cfg = _cfg()
    market = StubMarketData(closes=[100.0] * 5, price=100.0)
    eng = _engine(cfg, market, strategy=StubStrategy(Signal.BUY))
    eng.step()
    assert "BTC/USDT" in eng.positions
    eng.strategy = StubStrategy(Signal.SELL)
    eng.step()
    assert "BTC/USDT" not in eng.positions


def test_config_validation_rejects_bad_emas():
    try:
        _cfg(fast_ema=30, slow_ema=10)
    except ValueError:
        return
    raise AssertionError("expected ValueError for fast_ema >= slow_ema")
