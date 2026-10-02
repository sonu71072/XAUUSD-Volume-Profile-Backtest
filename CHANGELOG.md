# Changelog

All notable changes to this project are documented here.

---

## [V7] - 2026-10-03

### Added

- V7 POC-only strategy experiment
- Body ratio filter >= 0.70
- V7 full-sample backtest
- V7 chronological out-of-sample backtest
- V7 structural validation
- V7 OOS structural validation

### V7 Full-Sample Result

| Metric | Result |
|---|---:|
| Trades | 59 |
| Winners | 22 |
| Losers | 37 |
| Win Rate | 37.29% |
| Profit Factor | 1.19 |
| Total R | +7R |
| Expectancy | +0.119R |
| Max Drawdown | -5R |
| Max Loss Streak | 5 |

### V7 Out-of-Sample Result

OOS period:

`2025-09-12 → 2026-09-11`

| Metric | Result |
|---|---:|
| Trades | 27 |
| Winners | 9 |
| Losers | 18 |
| Win Rate | 33.33% |
| Profit Factor | 1.00 |
| Total R | 0.00R |
| Expectancy | 0.000R |
| Max Drawdown | -5R |
| Max Loss Streak | 5 |

### Research Conclusion

The V7 full-sample result was positive, but the chronological OOS result was 0R with a profit factor of 1.00.

V7 therefore does not establish a positive out-of-sample edge and is retained as a research experiment rather than a validated live-trading strategy.

---

## [V6] - 2026-10-03

### Added

- V6 body ratio threshold experiment
- Minimum candle body ratio of 0.70
- V6 out-of-sample backtest
- V6 OOS structural validation

### V6 OOS Result

| Metric | Result |
|---|---:|
| Trades | 46 |
| Winners | 16 |
| Losers | 30 |
| Win Rate | 34.78% |
| Profit Factor | 1.07 |
| Total R | +2R |
| Expectancy | +0.043R |
| Max Drawdown | -6R |
| Max Loss Streak | 5 |

### Session Breakdown

| Session | Trades | Total R |
|---|---:|---:|
| MORNING | 20 | +4R |
| US_OPEN | 26 | -2R |

### Direction Breakdown

| Direction | Trades | Total R |
|---|---:|---:|
| BUY | 23 | +10R |
| SELL | 23 | -8R |

---

## [V5] - 2026-10-03

### Added

- V5 candle body confirmation filter
- Minimum body ratio of 0.50
- V5 full-sample validation
- V5 chronological OOS validation

### V5 Full-Sample Result

| Metric | Result |
|---|---:|
| Trades | 113 |
| Win Rate | 30.09% |
| Profit Factor | 0.86 |
| Total R | -11R |
| Expectancy | -0.097R |
| Max Drawdown | -20R |
| Max Loss Streak | 10 |

### V5 OOS Result

| Metric | Result |
|---|---:|
| Trades | 53 |
| Win Rate | 28.30% |
| Profit Factor | 0.79 |
| Total R | -8R |
| Expectancy | -0.151R |
| Max Drawdown | -14R |
| Max Loss Streak | 10 |

---

## [V4] - 2026-10-03

### Added

- Chronological out-of-sample backtest
- Historical OOS period:
  `2025-09-12 → 2026-09-11`
- V4 OOS structural validation

### V4 OOS Result

| Metric | Result |
|---|---:|
| Trades | 60 |
| Winners | 17 |
| Losers | 43 |
| Win Rate | 28.33% |
| Profit Factor | 0.79 |
| Total R | -9R |
| Expectancy | -0.150R |
| Max Drawdown | -10R |
| Max Loss Streak | 6 |

### Research Note

The OOS period is a historical holdout used for research validation. It is not evidence of future or live performance.

---

## [V3] - 2026-10-03

### Added

- Hypothetical transaction-cost model
- Spread sensitivity
- Commission sensitivity
- Slippage sensitivity
- V3 transaction-cost analysis

### Cost Scenarios

| Scenario | Spread | Commission | Slippage |
|---|---:|---:|---:|
| Baseline | 0.00 | 0.00R | 0.00 |
| Low | 0.10 | 0.02R | 0.05 |
| Medium | 0.20 | 0.04R | 0.10 |
| High | 0.40 | 0.08R | 0.20 |

### Results

| Scenario | Total R | Profit Factor |
|---|---:|---:|
| Baseline | -18.74R | 0.79 |
| Low | -26.12R | 0.72 |
| Medium | -33.49R | 0.66 |
| High | -48.23R | 0.56 |

These are hypothetical sensitivity assumptions and are not broker-specific execution measurements.

---

## [V2] - 2026-10-03

### Added

- Causal/no-look-ahead strategy implementation
- Previous completed session profile
- Next-candle execution
- Fixed 2R target
- Fixed -1R stop
- One trade per session
- Maximum exit horizon
- Structural validation
- V2 audit

### V2 Result

| Metric | Result |
|---|---:|
| Trades | 124 |
| Winners | 35 |
| Losers | 89 |
| Win Rate | 28.23% |
| Profit Factor | 0.79 |
| Total R | -18.74R |
| Expectancy | -0.151R |
| Max Drawdown | -23.74R |
| Max Loss Streak | 7 |

### Research Note

V2 removed the look-ahead issue present in V1 by requiring the signal candle to close before entry.

---

## [1.0.0] - 2026-09-13

### Added

- Initial XAUUSD Volume Profile backtesting framework
- XAUUSD M5 data pipeline using MetaTrader 5
- Fixed Range Volume Profile calculation
- POC, VAH and VAL level generation
- Morning and US Open session detection
- V1 strategy implementation
- Trade-level backtest reporting
- $100,000 fixed-fractional risk simulation
- Research documentation and methodology notes

### V1 Research Notes

- V1 is the initial baseline research implementation.
- V1 contains a known look-ahead bias.
- V1 results are diagnostic only.
- Transaction costs, slippage and broker-specific execution effects were not modeled.

### V1 Baseline Result

| Metric | Result |
|---|---:|
| Signals | 846 |
| Closed Trades | 844 |
| Win Rate | 64.45% |
| Profit Factor | 3.63 |
| Total R | +788R |
| Expectancy | +0.934R |
| Max Drawdown | -6R |
| Max Loss Streak | 6 |

### Next Research Steps

- Remove look-ahead bias
- Introduce realistic execution assumptions
- Perform chronological OOS testing
- Perform robustness and sensitivity analysis