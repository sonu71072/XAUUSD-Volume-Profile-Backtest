import pandas as pd
import numpy as np

TRADES_FILE = "data/trades_v2.csv"

print("=" * 80)
print("V2.3 — TRADE AUDIT")
print("=" * 80)

# ============================================================
# LOAD TRADES
# ============================================================

trades = pd.read_csv(TRADES_FILE)

trades["signal_time"] = pd.to_datetime(trades["signal_time"])
trades["entry_time"] = pd.to_datetime(trades["entry_time"])
trades["exit_time"] = pd.to_datetime(trades["exit_time"])

print(f"Loaded trades : {len(trades):,}")

# ============================================================
# BASIC AUDIT
# ============================================================

print("\n" + "=" * 80)
print("1. EXIT REASON")
print("=" * 80)

exit_stats = trades.groupby("exit_reason").agg(
    trades=("pnl_R", "count"),
    total_R=("pnl_R", "sum"),
    avg_R=("pnl_R", "mean")
)

print(exit_stats.round(3))


# ============================================================
# SESSION AUDIT
# ============================================================

print("\n" + "=" * 80)
print("2. SESSION")
print("=" * 80)

session_stats = trades.groupby("session").agg(
    trades=("pnl_R", "count"),
    winners=("pnl_R", lambda x: (x > 0).sum()),
    losers=("pnl_R", lambda x: (x < 0).sum()),
    win_rate=("pnl_R", lambda x: (x > 0).mean() * 100),
    total_R=("pnl_R", "sum"),
    avg_R=("pnl_R", "mean")
)

print(session_stats.round(3))


# ============================================================
# DIRECTION AUDIT
# ============================================================

print("\n" + "=" * 80)
print("3. DIRECTION")
print("=" * 80)

direction_stats = trades.groupby("direction").agg(
    trades=("pnl_R", "count"),
    winners=("pnl_R", lambda x: (x > 0).sum()),
    losers=("pnl_R", lambda x: (x < 0).sum()),
    win_rate=("pnl_R", lambda x: (x > 0).mean() * 100),
    total_R=("pnl_R", "sum"),
    avg_R=("pnl_R", "mean")
)

print(direction_stats.round(3))


# ============================================================
# LEVEL AUDIT
# ============================================================

print("\n" + "=" * 80)
print("4. VOLUME PROFILE LEVEL")
print("=" * 80)

level_stats = trades.groupby("level").agg(
    trades=("pnl_R", "count"),
    winners=("pnl_R", lambda x: (x > 0).sum()),
    losers=("pnl_R", lambda x: (x < 0).sum()),
    win_rate=("pnl_R", lambda x: (x > 0).mean() * 100),
    total_R=("pnl_R", "sum"),
    avg_R=("pnl_R", "mean")
)

print(level_stats.round(3))


# ============================================================
# SESSION + LEVEL
# ============================================================

print("\n" + "=" * 80)
print("5. SESSION + LEVEL")
print("=" * 80)

combo = trades.groupby(
    ["session", "level"]
).agg(
    trades=("pnl_R", "count"),
    winners=("pnl_R", lambda x: (x > 0).sum()),
    win_rate=("pnl_R", lambda x: (x > 0).mean() * 100),
    total_R=("pnl_R", "sum"),
    avg_R=("pnl_R", "mean")
)

print(combo.round(3))


# ============================================================
# ENTRY GAP
# ============================================================

trades["entry_gap"] = (
    trades["entry"] - trades["level_price"]
)

print("\n" + "=" * 80)
print("6. ENTRY DISTANCE FROM PROFILE LEVEL")
print("=" * 80)

print(
    trades["entry_gap"].describe().round(4)
)


# ============================================================
# RISK / SL DISTANCE
# ============================================================

trades["risk_distance"] = abs(
    trades["entry"] - trades["sl"]
)

print("\n" + "=" * 80)
print("7. STOP DISTANCE")
print("=" * 80)

print(
    trades["risk_distance"].describe().round(4)
)


# ============================================================
# HOLDING TIME
# ============================================================

trades["holding_minutes"] = (
    trades["exit_time"] - trades["entry_time"]
).dt.total_seconds() / 60

print("\n" + "=" * 80)
print("8. HOLDING TIME")
print("=" * 80)

print(
    trades["holding_minutes"].describe().round(2)
)


# ============================================================
# SIGNAL -> ENTRY DELAY
# ============================================================

trades["signal_to_entry_minutes"] = (
    trades["entry_time"] - trades["signal_time"]
).dt.total_seconds() / 60

print("\n" + "=" * 80)
print("9. SIGNAL → ENTRY DELAY")
print("=" * 80)

print(
    trades["signal_to_entry_minutes"]
    .describe()
    .round(2)
)


# ============================================================
# WIN / LOSS DISTRIBUTION
# ============================================================

print("\n" + "=" * 80)
print("10. PNL DISTRIBUTION")
print("=" * 80)

print(
    trades["pnl_R"]
    .describe()
    .round(3)
)


# ============================================================
# WORST TRADES
# ============================================================

print("\n" + "=" * 80)
print("11. WORST 10 TRADES")
print("=" * 80)

worst = trades.sort_values(
    "pnl_R"
).head(10)

print(
    worst[
        [
            "signal_time",
            "session",
            "direction",
            "level",
            "entry",
            "sl",
            "tp",
            "exit",
            "exit_reason",
            "pnl_R"
        ]
    ].to_string(index=False)
)


# ============================================================
# BEST TRADES
# ============================================================

print("\n" + "=" * 80)
print("12. BEST 10 TRADES")
print("=" * 80)

best = trades.sort_values(
    "pnl_R",
    ascending=False
).head(10)

print(
    best[
        [
            "signal_time",
            "session",
            "direction",
            "level",
            "entry",
            "sl",
            "tp",
            "exit",
            "exit_reason",
            "pnl_R"
        ]
    ].to_string(index=False)
)


# ============================================================
# MONTHLY PERFORMANCE
# ============================================================

trades["month"] = trades["entry_time"].dt.to_period("M")

print("\n" + "=" * 80)
print("13. MONTHLY PERFORMANCE")
print("=" * 80)

monthly = trades.groupby("month").agg(
    trades=("pnl_R", "count"),
    win_rate=("pnl_R", lambda x: (x > 0).mean() * 100),
    total_R=("pnl_R", "sum"),
    avg_R=("pnl_R", "mean")
)

print(monthly.round(3))


# ============================================================
# FINAL DIAGNOSTIC
# ============================================================

print("\n" + "=" * 80)
print("V2.3 AUDIT COMPLETE")
print("=" * 80)

print("\nMain diagnostic questions:")
print("1. Is one session responsible for most losses?")
print("2. Is one profile level consistently weak?")
print("3. Is BUY or SELL materially weaker?")
print("4. Are TIME exits significant?")
print("5. Are stop distances unusually large?")
print("6. Is the next-candle entry creating adverse price movement?")
print("7. Is performance stable across months?")

print("\nNo strategy parameters were changed.")
print("This is an audit only.")