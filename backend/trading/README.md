# OctaStackTrader

A production-oriented crypto trading bot for NoblePort. It manages up to **8
concurrent long positions** (the "8 stack") across a configurable set of pairs
using a **10/30 EMA crossover** strategy with an **RSI filter**, fixed-percentage
**risk-based position sizing**, a **5% stop-loss**, and a **5% / 10% take-profit
ladder**.

It runs **paper (dry-run)** trading out of the box and **live** trading via any
[ccxt](https://github.com/ccxt/ccxt)-supported exchange (Binance, Kucoin,
Coinbase, …).

## Features

- **8-position limit** — never holds more than `MAX_POSITIONS` trades at once.
- **Multi-symbol** — configure any number of pairs (up to the stack limit held
  simultaneously).
- **Strategy** — 10/30 EMA crossover + RSI overbought/oversold filter.
- **Risk management** — fixed % risk per trade, 5% stop-loss, tiered take-profit
  (book half at +5%, the rest at +10% by default), minimum order notional.
- **Dry-run mode** — simulate trades against *live* prices with a virtual
  balance.
- **CSV trade logging** — every fill is recorded to `trading_log.csv`.
- **Dependency-light core** — indicators, strategy, risk and the paper broker
  are pure Python (no pandas/numpy); `ccxt` is only imported for live trading.

## Architecture

```
config.py      TradingConfig — env-driven, validated configuration
indicators.py  ema(), rsi() — pure-Python technical indicators
strategy.py    EmaCrossoverStrategy → Signal (BUY / SELL / HOLD)
risk.py        position sizing + stop-loss / take-profit price math
broker.py      Position, MarketData + Broker interfaces,
               PaperBroker (sim) and CCXT{MarketData,Broker} (live)
bot.py         OctaStackTrader — the engine (step() / run())
__main__.py    CLI wiring (ccxt feed → paper/live broker → engine)
```

Market **data** (read-only prices) is deliberately separated from order
**execution**, so paper trading reacts to real live prices while routing fills
to the simulated broker.

## Install

```bash
cd backend/trading
pip install -r requirements.txt   # ccxt + python-dotenv (live only)
cp .env.example .env              # then edit .env
```

The core can be imported and tested without installing anything.

## Configure

Edit `.env` (see `.env.example` for all options). Key settings:

| Variable            | Meaning                                              |
| ------------------- | ---------------------------------------------------- |
| `DRY_RUN`           | `true` = paper trading, `false` = real orders        |
| `TESTNET`           | use the exchange sandbox first                        |
| `SYMBOLS`           | comma-separated pairs, e.g. `BTC/USDT,ETH/USDT`       |
| `MAX_POSITIONS`     | the 8-stack limit                                     |
| `RISK_PER_TRADE`    | fraction of quote balance risked per trade           |
| `STOP_LOSS_PCT`     | stop distance below entry (default `0.05` = 5%)       |
| `TAKE_PROFIT_TIERS` | ladder `pct:fraction,...` (default `0.05:0.5,0.10:1.0`) |

## Run

From the repository root:

```bash
python -m backend.trading
```

Start with `DRY_RUN=true` and `TESTNET=true`. Only set `DRY_RUN=false` after you
have validated behaviour on the testnet with small size.

## Test

The test suite needs no third-party packages:

```bash
# with pytest
pytest backend/trading/tests/

# or without pytest
python -c "import inspect, backend.trading.tests.test_trading as t; \
[f() for n,f in inspect.getmembers(t, inspect.isfunction) if n.startswith('test_')]; \
print('ok')"
```

## Disclaimer

For educational purposes only. Cryptocurrency trading carries substantial risk.
Always test in dry-run / on a testnet and understand the strategy before
deploying real funds. The authors accept no responsibility for financial losses.
