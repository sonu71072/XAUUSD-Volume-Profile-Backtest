# V1 Research Notes

## 1. Research Objective

The objective of this project is to build a reproducible Python research framework for evaluating a mechanically defined XAUUSD M5 scalping strategy based on session-specific Fixed Range Volume Profile levels.

The project is not intended to establish profitability from a single historical backtest. The longer-term objective is to determine whether the strategy remains statistically and economically meaningful after controlling for information timing, transaction costs, execution assumptions, and out-of-sample performance.

---

## 2. Data

| Item | V1 configuration |
|---|---|
| Instrument | XAUUSD |
| Timeframe | M5 |
| Approx. candles | 139,751 |
| Historical period | Approximately 2 years |
| Source | MetaTrader 5 |
| Session timezone | Asia/Kolkata (IST) |

Market-closure/weekend gaps are retained as gaps rather than being filled with synthetic candles.

Because MT5 data is broker-dependent, another broker may produce different historical prices, candle availability, tick volumes, spreads, and contract specifications.

---

## 3. Session Definition

V1 uses two predefined sessions:

| Session | IST window |
|---|---:|
| Morning | 03:30–06:00 |
| US Open | 18:55–19:55 |

Weekdays are used for session-profile construction. Sessions with insufficient candle availability are excluded from profile generation.

---

## 4. Volume Profile Method

The Fixed Range Volume Profile is calculated over the candles belonging to each valid session.

### Configuration

- Number of price bins: **100**
- Value area: **70%**
- Volume input: **MT5 tick volume**

The output levels are:

- POC — Point of Control
- VAH — Value Area High
- VAL — Value Area Low

The implementation distributes candle volume across the price range represented by each candle rather than using exchange-traded centralized volume.

Therefore, the profile should be understood as a **broker/tick-volume-based research approximation**, not centralized exchange volume.

---

## 5. V1 Signal Model

### Long

1. Price touches a profile level within the configured tolerance.
2. Current candle closes above the level.
3. Previous candle closed at or below the level.
4. Stop loss is derived from the recent swing-low region.
5. Target is 2R.
6. One trade per session.

### Short

1. Price touches a profile level within the configured tolerance.
2. Current candle closes below the level.
3. Previous candle closed at or above the level.
4. Stop loss is derived from the recent swing-high region.
5. Target is 2R.
6. One trade per session.

### Parameters

```text
RR                 = 2.0
Level tolerance    = 0.50
Swing lookback     = 3 candles
Minimum SL         = 0.30
Maximum SL         = 15.00
One trade/session  = True
```

---

## 6. V1 Baseline Results

| Metric | Result |
|---|---:|
| Total signals | 846 |
| Closed trades | 844 |
| Open trades | 2 |
| Winners | 544 |
| Losers | 300 |
| Win rate | 64.45% |
| Profit factor | 3.63 |
| Net result | +788R |
| Expectancy | +0.934R |
| Max drawdown | -6R |
| Max consecutive losses | 6 |

### Session

- Morning: 376 trades, 63.30% win rate, +338R
- US Open: 468 trades, 65.38% win rate, +450R

### Profile level

- VAH: 364 trades, 65.11% win rate, +347R
- POC: 246 trades, 65.85% win rate, +240R
- VAL: 234 trades, 61.97% win rate, +201R

### Direction

- BUY: 463 trades, 66.31% win rate, +458R
- SELL: 381 trades, 62.20% win rate, +330R

---

## 7. $100K Fixed-Fractional Simulation

The separate capital model starts at $100,000 and risks 1% of the current balance on each closed trade.

| Metric | Result |
|---|---:|
| Starting capital | $100,000 |
| Risk/trade | 1% |
| Closed trades | 844 |
| Win rate | 64.45% |
| Profit factor | 3.31 |
| Total P&L | $233,811,631.31 |
| Final balance | $233,911,631.31 |
| Max drawdown | -$9,250,468.70 |
| Max loss streak | 6 |

This simulation is intentionally separated from the R-based strategy report because it represents a **hypothetical compounding model**, not actual brokerage P&L.

The enormous nominal growth should not be interpreted as a realistic forecast. Fixed-percentage compounding mathematically scales the dollar outcome as the simulated balance increases, while real-world execution, liquidity, margin, spread, slippage, and position-size constraints would materially change results.

---

## 8. Bias Audit — V1

### 8.1 Same-candle entry look-ahead bias

The original V1 implementation uses the current candle close to confirm a signal but records the entry at that same candle's open.

This is causally impossible because the candle's closing price is not known at the candle open.

Correct sequence:

```text
Candle forms
    ↓
Candle closes
    ↓
Signal becomes known
    ↓
Next candle opens
    ↓
Entry
```

This is the primary reason V1 is considered a **baseline rather than a validated result**.

### 8.2 Profile-information timing

The session profile implementation uses the session's candle data to calculate profile levels. When those levels are used for signals within the same session, the timing of profile availability must be reviewed carefully.

V2 must explicitly define **when the profile becomes known** and ensure no future session candles are used for a decision made earlier in the session.

### 8.3 Execution realism

V1 does not model:

- Bid/ask spread
- Commission
- Slippage
- Swap/financing
- Liquidity constraints
- Broker contract specifications
- Margin requirements

These are planned for later versions.

---

## 9. What V1 Establishes

V1 successfully establishes the research infrastructure needed for subsequent testing:

- Historical M5 data acquisition
- Session classification
- Session profile construction
- POC/VAH/VAL extraction
- Mechanical trade generation
- Trade-level exports
- Risk-based capital simulation
- Basic performance decomposition
- Explicit bias documentation

V1 does **not** establish that the strategy is profitable in live trading.

---

## 10. V2 Research Questions

V2 should answer:

1. Does the strategy remain profitable when entries occur only after signal confirmation?
2. Are profile levels available at the exact time the signal is generated?
3. How much performance disappears after removing future information?
4. Does the strategy survive realistic spread and slippage?
5. Does performance remain stable across sessions, months, and market regimes?
6. Does the edge survive out-of-sample data?

---

## 11. Validation Roadmap

```text
V1  Baseline implementation
 ↓
V2  Remove look-ahead / causal execution
 ↓
V3  Add spread + commission + slippage
 ↓
V4  Out-of-sample + walk-forward testing
 ↓
V5  Parameter sensitivity + Monte Carlo
 ↓
Final research conclusion
```

A strategy should only move toward deployment after surviving these validation stages.


---

---

## 12. V2 Causal Specification

V2 keeps V1 frozen as the historical baseline and introduces a separate causal specification.

The primary changes are:

1. Profile levels are derived from the previous completed session of the same session type.
2. A signal is confirmed only after the signal candle closes.
3. Entry occurs at the next candle open.
4. Stop-loss and take-profit remain based on the same 2R framework used in V1.
5. One trade per session is retained.

### V2.1 Profile Assumption

For each trading session, V2 uses the profile from the previous completed session of the same type.

For example:

```text
Previous MORNING session
        ↓
Calculate POC / VAH / VAL
        ↓
Next MORNING session
        ↓
Use those fixed levels for signals



---

## 13. V2 Causal Validation

The V2 implementation was subjected to structural validation before performance interpretation.

| Check | Result |
|---|---:|
| Trades | 124 |
| Profiles | 913 |
| Signal to entry delay | 5.00 min |
| Valid previous profiles | 124 / 124 |
| Missing profile dates | 0 |
| Duplicate session profiles | 0 |
| Valid entries | 124 / 124 |
| BUY SL valid | 54 / 54 |
| BUY TP valid | 54 / 54 |
| SELL SL valid | 70 / 70 |
| SELL TP valid | 70 / 70 |
| RR min | 2.000 |
| RR max | 2.000 |
| RR mean | 2.000 |
| Sessions with more than 1 trade | 0 |
| Valid exits | 124 / 124 |
| Maximum P&L calculation difference | 0 |

### Final Validation Status

```text
V2.2 CAUSAL VALIDATION: PASSED


```

All structural validation checks passed.

Structural validation passing does not establish profitability.




---

## 14. V2 Performance Results

The V2 specification generated substantially fewer trades than V1.

| Metric | V1 | V2 |
|---|---:|---:|
| Trades | 846 | 124 |
| Win rate | 64.30% | 28.23% |
| Total R | +788.00R | -18.74R |
| Average R | +0.934R | -0.151R |
| Profit factor | 3.63 | 0.79 |
| Max drawdown | -6.00R | -23.74R |

### V2 Session Breakdown

| Session | Trades | Total R | Average R |
|---|---:|---:|---:|
| MORNING | 46 | +2.256R | +0.049R |
| US OPEN | 78 | -21.000R | -0.269R |

### V2 Direction Breakdown

| Direction | Trades | Total R | Average R |
|---|---:|---:|---:|
| BUY | 54 | -3.000R | -0.056R |
| SELL | 70 | -15.744R | -0.225R |

### V2 Profile-Level Breakdown

| Level | Trades | Total R | Average R |
|---|---:|---:|---:|
| POC | 41 | -4.744R | -0.116R |
| VAH | 44 | -8.000R | -0.182R |
| VAL | 39 | -6.000R | -0.154R |

### V2 Exit Breakdown

| Exit | Trades | R contribution |
|---|---:|---:|
| Stop Loss | 88 | -88R |
| Take Profit | 35 | +70R |
| Time Exit | 1 | -0.744R |

Average entry delay was exactly 5 minutes for all V2 trades because entries occur at the next M5 candle open.



---

## 15. V1 vs V2 Interpretation

The V2 results should not be described simply as the cost of look-ahead bias.

V2 makes two material methodological changes:

1. It removes the same-candle signal-confirmation/entry inconsistency present in V1.
2. It replaces the same-session profile construction with a previous-completed-session profile specification.

Therefore, the change from V1 to V2 measures the effect of moving to a more causal research specification, not an isolated estimate of look-ahead bias alone.

The current V2 specification produces fewer signals, negative expectancy, negative total R, and a profit factor below 1.

V2 should be treated as a research milestone rather than a final conclusion because the profile timing rule is itself a provisional specification and has not been established as the exact methodology of the reference strategy.



---

## 16. Current Research Status

```text
V1
Baseline implementation
        ↓
V2
Causal execution + previous-session profile
        ↓
V2 Validation
PASSED
        ↓
Current result
Negative expectancy
        ↓
Next research stage
Transaction-cost modelling