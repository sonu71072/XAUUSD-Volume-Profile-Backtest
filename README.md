# XAUUSD Volume Profile Backtest

A Python quantitative-research framework for studying XAUUSD (Gold) M5 scalping using session-based Fixed Range Volume Profile.

> \*\*Status:\*\* V7 research experiment. The current V7 rules have \*\*not established a positive out-of-sample edge\*\* and are not considered validated live-trading rules.

\---

## Research Pipeline

```text
MT5
 ↓
M5 Historical Data
 ↓
Session Detection
 ↓
Fixed Range Volume Profile
 ↓
POC / VAH / VAL
 ↓
Mechanical Signal Engine
 ↓
Trade Simulation
 ↓
Cost / OOS / Structural Validation
```

\---

## Objective

The objective of this project is to investigate whether XAUUSD price reactions around **Volume Profile levels** can be converted into systematic, mechanical and reproducible trading rules.

The research focuses on:

* Point of Control (POC)
* Value Area High (VAH)
* Value Area Low (VAL)
* Session-based Volume Profiles
* Candle confirmation
* Fixed risk/reward
* No-look-ahead execution
* Transaction-cost sensitivity
* Chronological out-of-sample testing
* Structural validation
* Strategy robustness

The project is intentionally built as a research framework rather than as a claim of guaranteed trading performance.

\---

# Data

* **Instrument:** XAUUSD
* **Timeframe:** M5
* **Data Source:** MetaTrader 5
* **Historical Sample:** Approximately 2 years
* **Session Timezone:** Asia/Kolkata
* **Volume:** Tick volume
* **Raw CSV Data:** Excluded from GitHub through `.gitignore`

The historical dataset used during the research contained approximately **139,751 M5 candles**.

Missing candles were not filled with synthetic data.

Most gaps were associated with market closures and weekends.

\---

# Trading Sessions

The research currently uses two predefined trading sessions.

|Session|IST|
|-|-|
|MORNING|03:30–06:00|
|US\_OPEN|18:55–19:55|

Only valid weekday session data is used.

The session engine converts source timestamps into the research timezone before applying session rules.

\---

# Fixed Range Volume Profile

The project calculates a session-based Fixed Range Volume Profile.

Baseline configuration:

* **100 price bins**
* **70% value area**
* **POC — Point of Control**
* **VAH — Value Area High**
* **VAL — Value Area Low**
* Tick volume as the available volume proxy

The resulting profile levels are then used by the strategy engine to generate mechanical trading signals.

\---

# Research Methodology

The project follows a versioned research process.

Each strategy version is preserved separately so that changes can be compared and reproduced.

The general process is:

1. Build the initial hypothesis
2. Test the strategy
3. Audit for look-ahead bias
4. Convert the strategy to causal execution
5. Model transaction costs
6. Test chronologically out-of-sample
7. Introduce predefined experiments
8. Validate structural correctness
9. Document the results
10. Continue research based on the evidence

A positive result on historical data is not automatically treated as evidence of robustness.

\---

# V1 — Initial Baseline

V1 was the original mechanical implementation based on Volume Profile interactions.

The strategy searched for interactions with:

* POC
* VAH
* VAL

and applied candle confirmation, stop-loss rules, a 2R target, one trade per session and exit constraints.

## Critical Research Limitation

The original V1 implementation contained a **look-ahead bias**.

The signal candle's close was used for confirmation while execution was modeled using that same candle's open.

Therefore, V1 performance numbers are **diagnostic only**.

They should not be interpreted as live-tradable performance.

## V1 Result

|Metric|Result|
|-|-:|
|Signals|846|
|Closed Trades|844|
|Win Rate|64.45%|
|Profit Factor|3.63|
|Total R|+788R|
|Expectancy|+0.934R|
|Max Drawdown|-6R|
|Max Loss Streak|6|

V1 is retained as the historical baseline against which later versions can be compared.

\---

# V2 — Causal / No-Look-Ahead Strategy

V2 was created to remove the execution bias identified in V1.

Key changes:

* Previous completed session used for profile
* Signal candle must close before confirmation
* Entry occurs on the following candle
* Fixed 2R target
* Fixed -1R stop
* One trade per session
* Maximum exit horizon
* Structural validation

## V2 Result

|Metric|Result|
|-|-:|
|Trades|124|
|Winners|35|
|Losers|89|
|Win Rate|28.23%|
|Profit Factor|0.79|
|Total R|-18.74R|
|Expectancy|-0.151R|
|Max Drawdown|-23.74R|
|Max Loss Streak|7|

The V2 results demonstrated why causal execution and look-ahead auditing are important in this research.

\---

# V3 — Transaction Cost Model

V3 introduced a hypothetical transaction-cost sensitivity model.

The model tested different combinations of:

* Spread
* Commission
* Slippage

## Cost Assumptions

|Scenario|Spread|Commission|Slippage|
|-|-:|-:|-:|
|Baseline|0.00|0.00R|0.00|
|Low|0.10|0.02R|0.05|
|Medium|0.20|0.04R|0.10|
|High|0.40|0.08R|0.20|

## V3 Results

|Scenario|Total R|Profit Factor|
|-|-:|-:|
|Baseline|-18.74R|0.79|
|Low|-26.12R|0.72|
|Medium|-33.49R|0.66|
|High|-48.23R|0.56|

These are hypothetical sensitivity assumptions.

They are **not broker-specific execution measurements**.

\---

# V4 — Out-of-Sample Validation

V4 introduced chronological out-of-sample testing.

## OOS Period

```text
2025-09-12 → 2026-09-11
```

## V4 OOS Result

|Metric|Result|
|-|-:|
|Trades|60|
|Winners|17|
|Losers|43|
|Win Rate|28.33%|
|Profit Factor|0.79|
|Total R|-9R|
|Expectancy|-0.150R|
|Max Drawdown|-10R|
|Max Loss Streak|6|

The OOS period is a historical holdout used for research validation.

It is not evidence of future or live performance.

\---

# V5 — Candle Body Confirmation

V5 introduced a minimum candle body-ratio filter.

```text
Body Ratio >= 0.50
```

The purpose was to test whether stronger candle bodies would improve the quality of the causal setup.

## V5 Full-Sample Result

|Metric|Result|
|-|-:|
|Trades|113|
|Win Rate|30.09%|
|Profit Factor|0.86|
|Total R|-11R|
|Expectancy|-0.097R|
|Max Drawdown|-20R|
|Max Loss Streak|10|

## V5 OOS Result

|Metric|Result|
|-|-:|
|Trades|53|
|Win Rate|28.30%|
|Profit Factor|0.79|
|Total R|-8R|
|Expectancy|-0.151R|
|Max Drawdown|-14R|
|Max Loss Streak|10|

Both full-sample and OOS structural validation passed.

\---

# V6 — Stronger Body Ratio Filter

V6 increased the body-ratio threshold:

```text
Body Ratio >= 0.70
```

This experiment retained the causal execution framework while testing a stricter candle-confirmation condition.

## V6 OOS Result

|Metric|Result|
|-|-:|
|Trades|46|
|Winners|16|
|Losers|30|
|Win Rate|34.78%|
|Profit Factor|1.07|
|Total R|+2R|
|Expectancy|+0.043R|
|Max Drawdown|-6R|
|Max Loss Streak|5|

### Session Breakdown

|Session|Trades|Total R|Mean R|
|-|-:|-:|-:|
|MORNING|20|+4R|+0.200R|
|US\_OPEN|26|-2R|-0.077R|

### Direction Breakdown

|Direction|Trades|Total R|Mean R|
|-|-:|-:|-:|
|BUY|23|+10R|+0.435R|
|SELL|23|-8R|-0.348R|

V6 OOS structural validation passed.

\---

# V7 — POC-Only Experiment

V7 further restricted the setup to **POC only**.

The V7 experiment retained:

```text
Body Ratio >= 0.70
```

and removed VAH/VAL entries from the tested level set.

Therefore:

```text
Level = POC only
```

\---

## V7 Full-Sample Result

|Metric|Result|
|-|-:|
|Trades|59|
|Winners|22|
|Losers|37|
|Win Rate|37.29%|
|Profit Factor|1.19|
|Total R|+7R|
|Expectancy|+0.119R|
|Max Drawdown|-5R|
|Max Loss Streak|5|

### V7 Session Breakdown

|Session|Trades|Total R|Mean R|
|-|-:|-:|-:|
|MORNING|25|+8R|+0.320R|
|US\_OPEN|34|-1R|-0.029R|

### V7 Direction Breakdown

|Direction|Trades|Total R|Mean R|
|-|-:|-:|-:|
|BUY|29|+4R|+0.138R|
|SELL|30|+3R|+0.100R|

The full-sample result is retained as a research observation.

It is not sufficient by itself to establish robustness.

\---

# V7 Out-of-Sample Validation

The V7 chronological OOS test uses:

```text
OOS Period:
2025-09-12 → 2026-09-11
```

## OOS Dataset

|Metric|Result|
|-|-:|
|OOS Candles|69,335|
|OOS Session Candles|6,678|

## V7 OOS Performance

|Metric|Result|
|-|-:|
|Total Trades|27|
|Winners|9|
|Losers|18|
|Win Rate|33.33%|
|Profit Factor|1.00|
|Total R|0.00R|
|Expectancy|0.000R|
|Max Drawdown|-5.00R|
|Max Loss Streak|5|

### Session Breakdown

|Session|Trades|Total R|Mean R|
|-|-:|-:|-:|
|MORNING|13|+2.00R|+0.154R|
|US\_OPEN|14|-2.00R|-0.143R|

### Direction Breakdown

|Direction|Trades|Total R|Mean R|
|-|-:|-:|-:|
|BUY|15|+6.00R|+0.400R|
|SELL|12|-6.00R|-0.500R|

### Level Breakdown

|Level|Trades|Total R|Mean R|
|-|-:|-:|-:|
|POC|27|0.00R|0.000R|

### Exit Breakdown

|Exit|Trades|Total R|
|-|-:|-:|
|SL|18|-18R|
|TP|9|+18R|

### Body Ratio

|Statistic|Value|
|-|-:|
|Minimum|0.704150|
|Mean|0.790488|
|Maximum|1.000000|

\---

# Current Research Conclusion

The current V7 experiment **does not establish a positive out-of-sample edge**.

The full historical sample produced:

```text
Total R: +7R
Profit Factor: 1.19
```

while the chronological OOS sample produced:

```text
Total R: 0.00R
Profit Factor: 1.00
Expectancy: 0.000R
```

Therefore, the current V7 strategy remains a **research experiment** rather than a validated trading strategy.

The result does not determine whether future market behavior will be similar to the historical sample.

Further research is required to evaluate robustness.

\---

# Structural Validation

The project includes automated validation scripts designed to identify implementation and data-timing problems.

Validation checks include:

* Profile generated before session
* Profile date matches source data
* All required profiles found
* Signal occurs before or at entry
* Entry occurs after signal confirmation
* Entry delay is exactly 5 minutes
* One trade per session
* TP equals +2R
* SL equals -1R
* Exit occurs after entry
* Valid exit reasons
* P\&L consistency
* Body ratio is present
* Body ratio filter is enforced
* Body ratio calculation is consistent
* Stored profile date is valid
* OOS trades remain inside the OOS period

## V7 Validation Status

```text
V7 STRUCTURAL VALIDATION: PASSED

V7 OOS STRUCTURAL VALIDATION: PASSED
```



\## V8 — POC Distance Filter Experiment



V8 extends the V7 POC-only strategy by adding a predefined entry-distance filter.



\### V8 Rules



V8 keeps the V7 framework unchanged:



\- Previous completed session profile

\- POC-only level

\- Body ratio >= 0.70

\- Signal confirmation

\- Next-candle-open execution

\- 2R take-profit

\- 1R stop-loss

\- One trade per session

\- Causal profile construction

\- Chronological OOS validation



Additional V8 condition:



```text

POC Distance Risk = |Entry - POC| / |Entry - Stop Loss|



Trade is accepted only when:



POC Distance Risk <= 0.20R



The 0.20R threshold was derived from the full-sample V7 distance analysis and therefore must not be treated as an independently discovered OOS parameter.



V8 Full-Sample Result

Metric	Result

Trades	31

Winners	15

Losers	16

Win Rate	48.39%

Profit Factor	1.88

Total R	+14.00R

Expectancy	+0.452R

Max Drawdown	-4.00R

Max Loss Streak	4





V8 Out-of-Sample Result

OOS period:

2025-09-12 → 2026-09-12



Metric	Result

Trades	13

Win Rate	53.85%

Profit Factor	2.33

Total R	+8.00R

Expectancy	+0.615R

Max Drawdown	-2.00R





V8 OOS structural validation passed.

Interpretation

V8 produced positive results in both the full-sample test and the historical out-of-sample holdout.

However, the POC-distance threshold was selected using full-sample analysis. Therefore, the V8 full-sample improvement is not independent evidence.

The OOS result provides historical evidence under the tested period and methodology, but it does not establish future or live trading profitability.

Further validation should include additional unseen data, parameter sensitivity testing, and realistic transaction-cost assumptions.



\*\*Abhi commit mat karna.\*\*



README save karne ke baad bas mujhe \*\*`Done`\*\* bolna. Phir hum `CHANGELOG.md` update karenge.









Passing structural validation means the implementation satisfied the defined mechanical checks.

It does **not** mean that the strategy is profitable or validated for live trading.

\---

# Project Structure

```text
XAUUSD-Volume-Profile-Backtest/
│
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── requirements.txt
├── CHANGELOG.md
├── .gitignore
│
├── docs/
│   ├── RESEARCH\_NOTES.md
│   └── GITHUB\_UPLOAD.md
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
└── tests/
    └── test\_volume\_profile.py
```

Historical versions are intentionally preserved as separate research experiments to maintain reproducibility.

\---

# Installation

Clone the repository:

```bash
git clone https://github.com/sonu71072/XAUUSD-Volume-Profile-Backtest.git
```

Move into the project:

```bash
cd XAUUSD-Volume-Profile-Backtest
```

Install dependencies:

```bash
pip install -r requirements.txt
```

\---

# Research Pipeline Commands

## Data

```bash
python -m src.fetch\_data
```

## Session Engine

```bash
python -m src.session\_engine
```

## Session Profile

```bash
python -m src.session\_profile
```

## Visual Strategy Check

```bash
python -m src.strategy\_visual\_check
```

## V1 Strategy

```bash
python -m src.strategy
```

## $100k Simulation

```bash
python -m src.backtest\_100k
```

\---

# V7 Commands

Run the V7 strategy:

```bash
python -m src.v7\_strategy
```

Run structural validation:

```bash
python -m src.v7\_validation
```

Run chronological OOS backtest:

```bash
python -m src.v7\_oos\_backtest
```

Run OOS validation:

```bash
python -m src.v7\_oos\_validation
```

\---

# Research Standards

The project follows a research-first methodology.

Important standards include:

* No look-ahead bias
* Causal trade execution
* Chronological OOS testing
* Structural validation
* Transaction-cost sensitivity
* Parameter sensitivity
* Drawdown reporting
* Trade-level analysis
* Explicit assumptions
* Reproducible experiments
* Versioned strategy development

Future research areas may include:

* Walk-forward validation
* Parameter sensitivity analysis
* Monte Carlo trade-sequence analysis
* Regime analysis
* More realistic broker execution modeling
* Larger independent datasets
* Robustness testing

\---

# Limitations

Backtest results depend on assumptions and historical data.

Important limitations include:

* Historical data quality
* Tick-volume representation
* Session definitions
* Spread assumptions
* Slippage assumptions
* Commission assumptions
* Stop/target execution assumptions
* Broker-specific contract specifications
* Historical market regime
* Parameter selection

Backtests cannot guarantee future performance.

\---

# $100,000 Risk Simulation

The project also contains a theoretical fixed-fractional risk simulation.

The model can use:

* Starting capital: $100,000
* Risk per trade: 1%
* Target: 2R
* Compounding

This simulation is intended for quantitative research.

It is **not broker-level P\&L**.

Actual XAUUSD trading results depend on factors such as:

* Contract size
* Lot size
* Spread
* Commission
* Slippage
* Swap
* Leverage
* Execution quality

\---

# Repository Philosophy

This project is built around:

```text
TEST
 ↓
VERIFY
 ↓
DOCUMENT
 ↓
VERSION
 ↓
COMPARE
 ↓
RESEARCH
```

A strategy is not considered successful simply because a backtest produces a positive historical result.

The goal is to determine whether the result survives:

* Causal execution
* Costs
* Out-of-sample testing
* Structural validation
* Robustness analysis

\---

# Disclaimer

This repository is intended for educational and quantitative research purposes only.

Nothing in this project constitutes financial advice, investment advice, or a guarantee of future trading performance.

Past backtest results do not guarantee future results.

\---

# Author

**Sonu Kumar**

GitHub:

https://github.com/sonu71072/XAUUSD-Volume-Profile-Backtest

