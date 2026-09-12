# Research Notes

## Baseline

XAUUSD M5 data from MetaTrader 5 is segmented into Morning (03:30–06:00 IST) and US Open (18:55–19:55 IST) sessions. A Fixed Range Volume Profile uses 100 bins and a 70% value area to derive POC, VAH and VAL.

## V1

The initial mechanical baseline produced 846 signals and 844 closed trades, reported as +788R.

However, it uses the signal candle close for confirmation while entering at that candle's open. This is look-ahead bias. The V1 result is therefore diagnostic only.

## Validation Sequence

1. Close the confirmation candle.
2. Enter no earlier than the next candle.
3. Add spread, slippage and commission.
4. Freeze parameters.
5. Split development and out-of-sample data.
6. Run walk-forward validation.
7. Perform sensitivity and Monte Carlo analysis.

Do not commit private MT5 credentials, API keys or account information.
