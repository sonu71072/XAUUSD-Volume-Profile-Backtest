# XAUUSD Volume Profile Backtest

A Python quantitative-research framework for studying XAUUSD (Gold) M5 scalping using session-based Fixed Range Volume Profile.

> **Status:** Provisional V1 research baseline. The V1 rules are a mechanical hypothesis and are **not** claimed to be an exact reproduction of any third-party strategy.

## Objective

Test whether XAUUSD price reactions around **POC, VAH and VAL** can be converted into systematic, reproducible trading rules.

```text
MT5 → M5 Data → Session Detection → Volume Profile
   → POC / VAH / VAL → Signal Engine → Trade Simulation
   → Risk / Equity Analysis
```

## Data

- Instrument: XAUUSD
- Timeframe: M5
- Source: MetaTrader 5
- Historical sample: approximately two years
- Session timezone: Asia/Kolkata
- Raw CSV data is excluded from GitHub by `.gitignore`.

### Sessions

| Session | IST |
|---|---|
| Morning | 03:30–06:00 |
| US Open | 18:55–19:55 |

Broker market availability can shorten individual sessions. Missing candles are not filled with synthetic data.

## Volume Profile

Baseline settings:

- 100 price bins
- 70% value area
- POC — Point of Control
- VAH — Value Area High
- VAL — Value Area Low
- Tick volume as the available volume proxy

## V1 Baseline Strategy

The baseline searches for interactions with POC/VAH/VAL and applies candle confirmation, swing-based stops, a 2R target, one trade per session, stop-distance constraints, and a maximum exit horizon.

### Critical Research Limitation: Look-Ahead Bias

The original V1 implementation uses the signal candle's **close** for confirmation while entering at that same candle's **open**. This is look-ahead bias.

Therefore the V1 performance numbers below are **diagnostic only and must not be treated as live-tradable performance**.

The next milestone is a strict no-look-ahead version: confirmation candle closes first, then entry can occur on the following candle.

## V1 Baseline Result

| Metric | Result |
|---|---:|
| Signals | 846 |
| Closed trades | 844 |
| Win rate | 64.45% |
| Profit factor | 3.63 |
| Net R | +788R |
| Expectancy | +0.934R |
| Max drawdown | -6R |
| Max consecutive losses | 6 |

These numbers are retained only as a baseline benchmark because of the look-ahead issue.

## $100,000 Risk Model

A separate theoretical simulation can model:

- Starting capital: $100,000
- Risk: 1% per trade
- Target: 2R
- Compounding: enabled

This is not broker-level P&L. Real XAUUSD P&L depends on contract size, lot size, spread, commission, swap, slippage and execution.

## Project Structure

```text
XAUUSD-Volume-Profile-Backtest/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── requirements.txt
├── .gitignore
├── docs/
│   ├── RESEARCH_NOTES.md
│   └── GITHUB_UPLOAD.md
├── src/
│   ├── fetch_data.py
│   ├── volume_profile.py
│   ├── session_engine.py
│   ├── session_profile.py
│   ├── strategy_visual_check.py
│   ├── strategy.py
│   └── backtest_100k.py
└── tests/
    └── test_volume_profile.py
```

## Installation

```bash
git clone https://github.com/sonu71072/XAUUSD-Volume-Profile-Backtest.git
cd XAUUSD-Volume-Profile-Backtest
pip install -r requirements.txt
```

## Research Pipeline

After the code is placed under `src/`:

```bash
python src/fetch_data.py
python src/session_engine.py
python src/session_profile.py
python src/strategy_visual_check.py
python src/strategy.py
python src/backtest_100k.py
```

## Research Standards

- No look-ahead bias
- Separate development and out-of-sample periods
- Realistic spread, slippage and commission
- Parameter sensitivity testing
- Walk-forward validation
- Drawdown reporting
- Monte Carlo trade-sequence analysis
- Explicit assumptions and reproducible runs

## Roadmap

- [x] MT5 M5 data ingestion
- [x] Session segmentation
- [x] Fixed Range Volume Profile
- [x] POC / VAH / VAL
- [x] Baseline V1 backtest
- [x] Visual inspection
- [ ] Remove look-ahead bias
- [ ] Add transaction costs
- [ ] Proper $100k equity simulation
- [ ] Out-of-sample testing
- [ ] Walk-forward validation
- [ ] Sensitivity analysis
- [ ] Monte Carlo analysis
- [ ] Professional performance report

## Disclaimer

For educational and quantitative research purposes only. Backtested results do not guarantee future performance and are not financial advice.

## Author

**Sonu Kumar**

LinkedIn: https://www.linkedin.com/in/sonu-kumar-48700225b
