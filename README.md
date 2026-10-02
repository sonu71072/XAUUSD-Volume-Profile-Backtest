# XAUUSD Volume Profile Backtest

A Python quantitative-research framework for studying XAUUSD (Gold) M5 scalping using session-based Fixed Range Volume Profile.

> **Research Status:** V7 experimental baseline. No positive out-of-sample edge has been established yet.

The project is designed around a reproducible research workflow:

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