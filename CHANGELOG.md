# Changelog

All notable changes to this project are documented here.

## [1.0.0] - 2026-09-13

### Added
- Initial XAUUSD Volume Profile backtesting framework
- XAUUSD M5 data pipeline using MetaTrader 5
- Fixed Range Volume Profile calculation
- POC, VAH and VAL level generation
- Morning and US Open session detection
- V1 strategy implementation
- Trade-level backtest reporting
- ,000 fixed-fractional risk simulation
- Research documentation and methodology notes

### Research Notes
- V1 is a baseline research implementation.
- V1 contains known look-ahead bias.
- V1 results are not considered validated live-trading performance.
- Transaction costs, slippage and broker-specific execution effects are not modeled.

### Next
- V2: No-look-ahead strategy implementation
- Realistic execution modeling
- Out-of-sample validation
- Walk-forward testing
- Robustness and sensitivity analysis
