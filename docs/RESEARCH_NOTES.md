# Research Notes — XAUUSD Volume Profile Backtest

This document records the research evolution of the XAUUSD Volume Profile strategy from the original V1 implementation through the V7 experimental framework.

The purpose of this document is to preserve:

* strategy assumptions
* data methodology
* execution logic
* validation procedures
* transaction-cost assumptions
* out-of-sample testing
* experimental modifications
* structural validation
* limitations
* conclusions from each research stage

The versions are intentionally preserved separately so that previous experiments remain reproducible.

\---

# 1\. Research Objective

The objective of this project is to investigate whether a mechanical XAUUSD trading strategy based on:

* Fixed Range Volume Profile
* Point of Control (POC)
* Value Area High (VAH)
* Value Area Low (VAL)
* session-based market structure
* price interaction with volume-profile levels
* candle confirmation
* predefined risk/reward

can produce a repeatable trading edge when evaluated using historical M5 data.

The project is research-oriented.

A positive backtest result is not treated as proof of future profitability.

The workflow is:

```text
DATA
 ↓
PROFILE
 ↓
SIGNAL
 ↓
EXECUTION
 ↓
BACKTEST
 ↓
COST MODEL
 ↓
OUT-OF-SAMPLE
 ↓
STRUCTURAL VALIDATION
 ↓
RESEARCH CONCLUSION



2. Data Source
Historical market data is collected from MetaTrader 5.
Instrument:
XAUUSD

Timeframe:
M5

Historical period:
2024-09-12 → 2026-09-11

Total candles:
139,751

The dataset contains:
- Open
- High
- Low
- Close
- Tick Volume
- Time
Data is downloaded through the MT5 Python API.
The research does not fill weekend or market-closure gaps artificially.
3. Data Quality Checks
Before strategy testing, the historical dataset was checked for:
- duplicate timestamps
- chronological ordering
- missing timestamps
- invalid OHLC values
- timezone consistency
- market-session boundaries
Observed gaps are primarily associated with:
- weekends
- market closures
- unavailable trading periods
The dataset was therefore retained without artificially generating missing candles.
4. Timezone Handling
MT5 timestamps are handled in UTC.
Session definitions are converted to India Standard Time (IST).
Timezone conversion is performed explicitly rather than assuming that the source timestamps already represent local time.
Research sessions:
MORNING
03:30 – 06:00 IST

US\_OPEN
18:55 – 19:55 IST

Only weekdays are considered for session generation.
5. Session Detection
The session engine identifies M5 candles belonging to the predefined trading windows.
For every valid session, the following information can be derived:
- session date
- session type
- session start
- session end
- session candles
- session high
- session low
- session volume
Sessions with insufficient candles are excluded from profile construction.
Example:
MORNING
03:30 → 06:00 IST

US\_OPEN
18:55 → 19:55 IST

The session engine is responsible only for identifying the correct market window.
Strategy logic is handled separately.
6. Fixed Range Volume Profile
The project uses a Fixed Range Volume Profile.
The profile is constructed over the selected session range.
The price range is divided into:
100 price bins

Tick volume is distributed across the price structure according to the project implementation.
The resulting profile is used to identify:
- POC
- VAH
- VAL
7. Point of Control
The Point of Control (POC) is the price area with the highest accumulated volume within the selected profile.
Conceptually:
Highest Volume Price
        ↓
       POC

POC is used as a potential market reference level.
The strategy does not assume that every interaction with POC automatically produces a valid trade.
Additional signal conditions are applied depending on the strategy version.
8. Value Area
The project uses a 70% value-area concept.
The resulting levels are:
VAH = Value Area High
POC = Point of Control
VAL = Value Area Low

Conceptually:
VAH
────────────
     ↑
 Value Area
     ↓
────────────
POC
────────────
     ↓
 Value Area
     ↑
────────────
VAL

V1–V6 experiments evaluate different combinations of these profile levels.
V7 restricts the setup to POC only.
9. Original V1 Research Baseline
V1 was the initial strategy implementation.
The objective was to establish a baseline before introducing stricter causal execution and validation.
V1 used the current session profile and generated signals around profile levels.
This version produced very strong historical results:
Signals              : 846
Closed Trades        : 844
Win Rate             : 64.45%
Profit Factor        : 3.63
Total R              : +788R
Average R            : +0.934R
Maximum Drawdown     : -6R
Maximum Loss Streak  : 6

These results were treated as a research baseline rather than as proof of a tradable edge.
10. V1 $100k Simulation
A theoretical fixed-fractional simulation was also performed using:
Starting Balance : $100,000
Risk             : 1% of current balance per trade

Historical result:
Closed Trades    : 844
Win Rate         : 64.45%
Profit Factor    : 3.31
Final Balance    : $233,911,631.31
Total P\&L        : $233,811,631.31
Maximum Drawdown : -$9,250,468.70

This result is purely theoretical.
It assumes continuous compounding and does not represent realistic broker execution.
It should therefore not be interpreted as an achievable live-trading result.
11. Look-Ahead Bias Investigation
The extremely strong V1 performance required additional investigation.
The major research question became:
Does the strategy know information from the same session that would not have been available at the time of entry?

This led to the development of V2.
The goal was to remove potential look-ahead bias.
12. V2 — Causal Strategy
V2 changed the profile construction logic.
Instead of using the current session's completed profile, V2 uses:
Previous completed session
of the same session type

Example:
Current MORNING Session
        ↓
Use previous MORNING profile

Current US\_OPEN Session
        ↓
Use previous US\_OPEN profile

This ensures that the profile used for the signal existed before the trading session began.
13. V2 Execution Model
V2 introduced a causal execution framework.
Important rules:
- signal is generated only after candle close
- entry occurs on the next candle open
- profile must already exist
- no future candle information is used
- one trade per session
- predefined stop-loss
- predefined take-profit
- fixed risk/reward
Risk/reward:
Risk = 1R
Reward = 2R

Therefore:
SL = -1R
TP = +2R

Additional execution constraints include:
Swing Lookback : 3
Tolerance      : 0.50
Minimum SL     : 0.30
Maximum SL     : 15
Maximum Exit   : 300 candles

Same-candle SL/TP conflicts are resolved conservatively according to the strategy implementation.
14. V2 Results
The causal version produced significantly weaker results:
Trades          : 124
Winners         : 35
Losers          : 89
Win Rate        : 28.23%
Profit Factor   : 0.79
Total R         : -18.74R
Expectancy      : -0.151R
Maximum DD      : -23.74R
Max Loss Streak : 7

This was an important research result.
The original V1 performance was not preserved after causal execution was enforced.
15. V2 Structural Validation
The V2 implementation was tested for causal correctness.
Validation included:
- profile must exist before signal
- profile date must precede execution
- signal must occur before entry
- entry must occur after signal
- exactly one trade per session
- entry must precede exit
- TP must equal +2R
- SL must equal -1R
- P\&L must match exit reason
- valid exit reasons only
The structural validation passed.
This established V2 as a causal research implementation.
16. V3 — Transaction Cost Model
After establishing the causal framework, the next research question was:
How sensitive is the strategy to realistic trading costs?

V3 applied a hypothetical transaction-cost model to V2 trades.
The model included:
Spread
Commission
Slippage

Three cost environments were tested.
V3 Cost Scenarios
Baseline
Spread      : 0.00
Commission  : 0.00R
Slippage    : 0.00

Result:
Total R : -18.743965R
PF      : 0.788786

Low Cost
Spread      : 0.10
Commission  : 0.02R
Slippage    : 0.05

Result:
Total R : -26.116598R
PF      : 0.722615

Medium Cost
Spread      : 0.20
Commission  : 0.04R
Slippage    : 0.10

Result:
Total R : -33.489231R
PF      : 0.663634

High Cost
Spread      : 0.40
Commission  : 0.08R
Slippage    : 0.20

Result:
Total R : -48.234497R
PF      : 0.563012

These assumptions are hypothetical and are not broker-specific execution measurements.
17. V4 — Chronological Out-of-Sample Testing
V4 introduced a historical out-of-sample period.
OOS period:
2025-09-12 → 2026-09-11

The OOS period is separated chronologically from the earlier research data.
This prevents the strategy from being evaluated only on the same historical period used during development.
18. V4 OOS Results
Trades          : 60
Winners         : 17
Losers          : 43
Win Rate        : 28.33%
Profit Factor   : 0.79
Total R         : -9R
Expectancy      : -0.150R
Maximum DD      : -10R
Max Loss Streak : 6

The OOS result remained negative.
Therefore the causal strategy did not demonstrate a positive historical edge at this stage.
19. V4 Structural Validation
The V4 OOS implementation was checked for:
- chronological separation
- profile availability
- signal timing
- entry timing
- trade count consistency
- one trade per session
- correct SL/TP
- valid exit reasons
- P\&L consistency
The structural validation passed.
20. V5 — Candle Body Confirmation
V5 introduced a candle body confirmation filter.
Body ratio:
Body Ratio = abs(Close - Open) / (High - Low)

Minimum threshold:
Body Ratio >= 0.50

The objective was to remove weak candles and require stronger directional candle structure.
21. V5 Full-Sample Results
Trades          : 113
Winners         : 34
Losers          : 79
Win Rate        : 30.09%
Profit Factor   : 0.86
Total R         : -11R
Expectancy      : -0.097R
Maximum DD      : -20R
Max Loss Streak : 10

The filter reduced the number of trades but did not produce a positive result.
22. V5 OOS Results
Trades          : 53
Winners         : 15
Losers          : 38
Win Rate        : 28.30%
Profit Factor   : 0.79
Total R         : -8R
Expectancy      : -0.151R
Maximum DD      : -14R
Max Loss Streak : 10

The OOS result remained negative.
23. V5 Validation
Both full-sample and OOS structural validation passed.
The validation framework included:
- body ratio calculation
- body ratio threshold
- causal profile usage
- entry timing
- trade uniqueness
- SL/TP consistency
- exit ordering
- P\&L consistency
Same-candle exits were handled according to the execution model.
An entry candle may legitimately hit SL or TP depending on its OHLC range.
Therefore:
exit\_time >= entry\_time

is the correct validation rule rather than requiring:
exit\_time > entry\_time

24. V6 — Body Ratio Threshold 0.70
V6 increased the candle-strength requirement.
V5:
Body Ratio >= 0.50

V6:
Body Ratio >= 0.70

All other major causal framework components were kept consistent.
25. V6 OOS Results
Trades          : 46
Winners         : 16
Losers          : 30
Win Rate        : 34.78%
Profit Factor   : 1.07
Total R         : +2R
Expectancy      : +0.043R
Maximum DD      : -6R
Max Loss Streak : 5

Session breakdown:
MORNING
20 trades
+4R
Mean +0.200R

US\_OPEN
26 trades
-2R
Mean -0.077R

Direction breakdown:
BUY
23 trades
+10R
Mean +0.435R

SELL
23 trades
-8R
Mean -0.348R

Level breakdown:
POC
20 trades
+1R

VAH
14 trades
-2R

VAL
12 trades
+3R

The V6 OOS result was positive but small.
It was therefore treated as an experimental result requiring further testing rather than proof of a robust edge.
26. V6 Structural Validation
V6 OOS validation passed the causal and structural checks.
The validation confirmed:
- profile existed before session
- profile was found for every trade
- entry followed signal
- entry delay was exactly 5 minutes
- one trade per session
- TP = +2R
- SL = -1R
- exit occurred after entry or on the same entry candle
- valid exit reasons
- P\&L consistency
- body ratio was present
- body ratio threshold was respected
- body ratio calculation was consistent
27. V7 — POC-Only Experiment
V7 was designed as a predefined experiment based on the V6 framework.
V6 allowed:
POC
VAH
VAL

V7 restricted the strategy to:
POC only

The body confirmation remained:
Body Ratio >= 0.70

The purpose of V7 was to determine whether the observed V6 result was primarily associated with POC interactions.
28. V7 Full-Sample Results
Full historical sample:
Trades          : 59
Winners         : 22
Losers          : 37
Win Rate        : 37.29%
Profit Factor   : 1.19
Total R         : +7R
Expectancy      : +0.119R
Maximum DD      : -5R
Max Loss Streak : 5

Session breakdown:
MORNING
25 trades
+8R
Mean +0.320R

US\_OPEN
34 trades
-1R
Mean -0.029R

Direction breakdown:
BUY
29 trades
+4R
Mean +0.1379R

SELL
30 trades
+3R
Mean +0.100R

Level breakdown:
POC
59 trades
+7R
Mean +0.119R

Body ratio:
Minimum : 0.704150
Mean    : 0.837916
Maximum : 1.000000

The full-sample result was positive.
However, full-sample profitability alone is not sufficient to establish a reliable trading edge.
29. V7 Out-of-Sample Test
V7 was evaluated on the chronological OOS period:
2025-09-12 → 2026-09-11

OOS candles:
69,335

OOS session candles:
6,678

30. V7 OOS Results
Trades          : 27
Winners         : 9
Losers          : 18
Win Rate        : 33.33%
Profit Factor   : 1.00
Total R         : 0.00R
Expectancy      : 0.000R
Maximum DD      : -5R
Max Loss Streak : 5

Session breakdown:
MORNING
13 trades
+2R
Mean +0.154R

US\_OPEN
14 trades
-2R
Mean -0.143R

Direction breakdown:
BUY
15 trades
+6R
Mean +0.400R

SELL
12 trades
-6R
Mean -0.500R

Level breakdown:
POC
27 trades
0.00R
Mean 0.000R

Exit breakdown:
SL
18 trades
-18R

TP
9 trades
+18R

Body ratio:
Minimum : 0.704150
Mean    : 0.790488
Maximum : 1.000000

31. V7 Interpretation
The V7 full-sample result was:
+7R

while the chronological OOS result was:
0R

Therefore:
Positive full-sample result
        ≠
Established out-of-sample edge

The OOS test did not demonstrate a positive historical expectancy.
The correct research conclusion is:
V7 does not establish a robust positive out-of-sample edge.

This does not prove that the underlying market concept can never work.
It means that the current mechanical specification has not produced sufficient historical evidence to justify claiming a robust edge.
32. V7 Structural Validation
The V7 full-sample validation passed.
Validated conditions included:
trade\_count\_positive
profile\_before\_session
all\_profiles\_found
entry\_after\_signal
entry\_delay\_exactly\_5min
one\_trade\_per\_session
tp\_equals\_2R
sl\_equals\_minus\_1R
exit\_after\_entry
valid\_exit\_reasons
pnl\_consistency
body\_ratio\_present
body\_ratio\_filter\_70pct
body\_ratio\_calculation\_consistent
stored\_profile\_date\_valid

Final result:
V7 STRUCTURAL VALIDATION: PASSED

33. V7 OOS Structural Validation
The V7 OOS validation also passed.
Validated conditions included:
OOS period containment
profile before session
all profiles found
profile date matches source
entry after signal
entry delay exactly 5 minutes
one trade per session
TP = +2R
SL = -1R
exit after entry
valid exit reasons
P\&L consistency
body ratio present
body ratio >= 70%
body ratio calculation consistency
signal before/at entry
entry before/at exit

Final result:
V7 OOS STRUCTURAL VALIDATION: PASSED





\## V8 — POC Distance Filter Experiment



\### Objective



V8 tests whether restricting entries to cases where the entry price remains close to the selected POC improves the V7 POC-only setup.



\### Strategy Framework



V8 preserves the V7 causal framework:



\- Previous completed session profile

\- POC-only level

\- Body ratio >= 0.70

\- Signal confirmation

\- Next candle open execution

\- 2R take-profit

\- 1R stop-loss

\- One trade per session

\- Causal profile construction

\- Chronological OOS testing



\### Additional V8 Filter



The entry-to-POC distance is normalized by initial trade risk:



POC Distance Risk = |Entry - POC| / |Entry - Stop Loss|



Maximum accepted distance:



0.20R



Trades exceeding this threshold are rejected.



\### Full-Sample Results



| Metric | V8 |

|---|---:|

| Trades | 31 |

| Winners | 15 |

| Losers | 16 |

| Win Rate | 48.39% |

| Profit Factor | 1.88 |

| Total R | +14.00R |

| Expectancy | +0.452R |

| Max Drawdown | -4.00R |

| Max Loss Streak | 4 |



\### Out-of-Sample Results



OOS period:



2025-09-12 → 2026-09-12



| Metric | V8 OOS |

|---|---:|

| Trades | 13 |

| Win Rate | 53.85% |

| Profit Factor | 2.33 |

| Total R | +8.00R |

| Expectancy | +0.615R |

| Max Drawdown | -2.00R |



Structural validation passed.



\### Research Interpretation



V8 produced positive results on the tested full sample and historical OOS period.



However, the 0.20R POC-distance threshold was derived from full-sample analysis. Therefore, the full-sample result should not be treated as independent evidence.



The OOS result is a historical holdout result under the tested methodology. It does not establish future or live trading profitability.



Further research should test additional unseen periods, parameter sensitivity, and realistic transaction costs.

This is important because a negative or neutral result is still useful research if the implementation is structurally valid.
34. Research Evolution Summary
The overall research progression is:
V1
↓
Very strong historical result
↓
Look-ahead concern
↓
V2
↓
Causal execution
↓
Performance collapses
↓
V3
↓
Transaction-cost sensitivity
↓
V4
↓
Chronological OOS testing
↓
V5
↓
Body confirmation >= 0.50
↓
V6
↓
Body confirmation >= 0.70
↓
V7
↓
POC-only experiment
↓
OOS result = 0R

This progression demonstrates why each layer of validation is necessary.
35. Current Research Status
Current tested versions:
V1  Baseline
V2  Causal
V3  Cost Model
V4  OOS
V5  Body Ratio >= 0.50
V6  Body Ratio >= 0.70
V7  POC Only + Body Ratio >= 0.70

Current evidence:
V1
Very strong historical result
but not causal

V2
Negative

V3
Negative under costs

V4
Negative OOS

V5
Negative OOS

V6
Small positive OOS result

V7
Neutral OOS result

Therefore, the current project status is:
RESEARCH IN PROGRESS

A robust positive edge has not yet been established.
36. Important Research Principle
The project intentionally avoids selecting a strategy only because it produced the highest historical return.
Instead, the research process prioritizes:
1. Causal execution
2. No look-ahead
3. Structural validation
4. Transaction-cost sensitivity
5. Chronological OOS testing
6. Predefined experiments
7. Reproducibility
8. Honest interpretation
A strategy that performs well in-sample but fails OOS is not considered validated.
37. Reproducibility
Each strategy version is maintained separately.
This allows historical experiments to remain reproducible.
The repository intentionally contains:
v1
v2
v3
v4
v5
v6
v7

rather than overwriting older versions.
This prevents research history from being lost.
38. Project Structure
XAUUSD-Volume-Profile-Backtest/
│
├── src/
│   ├── fetch\_data.py
│   ├── volume\_profile.py
│   ├── session\_engine.py
│   ├── session\_profile.py
│   ├── strategy\_visual\_check.py
│   ├── strategy.py
│   ├── backtest\_100k.py
│   │
│   ├── session\_profile\_v2.py
│   ├── strategy\_v2.py
│   ├── v2\_audit.py
│   ├── v2\_validation.py
│   │
│   ├── v3\_cost\_model.py
│   │
│   ├── v4\_oos\_backtest.py
│   ├── v4\_validation.py
│   │
│   ├── v5\_strategy.py
│   ├── v5\_validation.py
│   ├── v5\_oos\_backtest.py
│   ├── v5\_oos\_validation.py
│   │
│   ├── v6\_strategy.py
│   ├── v6\_oos\_backtest.py
│   ├── v6\_oos\_validation.py
│   │
│   ├── v7\_strategy.py
│   ├── v7\_validation.py
│   ├── v7\_oos\_backtest.py
│   └── v7\_oos\_validation.py
│
├── tests/
│   └── test\_volume\_profile.py
│
├── docs/
│   ├── GITHUB\_UPLOAD.md
│   └── RESEARCH\_NOTES.md
│
├── data/
│   └── \*.csv
│
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── requirements.txt
└── .gitignore

39. Limitations
The current research has several limitations.
Historical Data
Backtests use historical market data.
Historical performance cannot guarantee future performance.
Tick Volume
The volume profile uses MT5 tick volume rather than centralized exchange volume.
Therefore, the volume distribution may differ from institutional or exchange-derived volume data.
Execution
Historical backtests cannot perfectly reproduce:
- spread changes
- slippage
- execution latency
- liquidity conditions
- broker-specific fills
- market gaps
Transaction Costs
V3 uses hypothetical cost assumptions.
They are not verified broker-specific execution costs.
Sample Size
Later experiments such as V6 and V7 contain relatively few OOS trades.
Small samples can produce unstable statistics.
Market Regime
The tested period represents only a limited historical market regime.
The strategy may behave differently under:
- high volatility
- low volatility
- news events
- changing liquidity
- structural market changes
40. What Would Count as Stronger Evidence?
Future research should ideally include:
- larger OOS samples
- multiple market regimes
- rolling walk-forward validation
- additional years of data
- realistic broker spread data
- realistic slippage assumptions
- Monte Carlo analysis
- parameter sensitivity analysis
- stability testing
- independent validation datasets
- forward testing
- paper trading
- execution-quality analysis
Parameter changes should be predefined before testing whenever possible.
41. Research Philosophy
The objective is not:
Find the backtest with the highest profit.

The objective is:
Find out whether a repeatable market relationship
survives increasingly realistic testing.

The research process therefore follows:
Hypothesis
   ↓
Implementation
   ↓
Backtest
   ↓
Audit
   ↓
Causal Validation
   ↓
Cost Model
   ↓
OOS Testing
   ↓
Structural Validation
   ↓
Interpretation

A failed experiment is still valuable if it eliminates a hypothesis.
42. Current Conclusion
The project has successfully progressed from an extremely strong but potentially biased V1 baseline to a causal and structurally validated research framework.
The major finding so far is:
Removing potential look-ahead and applying chronological out-of-sample testing materially reduces the apparent performance of the original strategy.

V6 produced a small positive OOS result, but V7 did not preserve that result after restricting the setup to POC-only.
Therefore:
No robust positive edge established yet.

The next strategy modification should be treated as a new research experiment rather than as a guaranteed improvement.
43. Final Research Rule
Every new strategy version should follow:
TEST
 ↓
VERIFY
 ↓
DOCUMENT
 ↓
GITHUB UPDATE
 ↓
NEXT EXPERIMENT

No strategy should be considered validated merely because its historical equity curve looks attractive.
The repository is intended to document the complete research process — including failed experiments, neutral results, and successful validation checks.
Disclaimer
This project is for educational and research purposes only.
Backtested results are hypothetical and do not guarantee future performance.
Nothing in this repository constitutes financial, investment, or trading advice.
Trading XAUUSD and leveraged derivatives involves substantial risk of loss.



