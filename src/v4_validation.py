import pandas as pd


# ============================================================
# V4 OOS STRUCTURAL VALIDATION
# ============================================================

TRADES_FILE = "data/trades_v4_oos.csv"
PROFILE_FILE = "data/session_profiles_v2.csv"

OOS_START = pd.Timestamp("2025-09-12").date()
OOS_END = pd.Timestamp("2026-09-11").date()

print()
print("=" * 80)
print("V4 OOS STRUCTURAL VALIDATION")
print("=" * 80)


# ============================================================
# LOAD
# ============================================================

trades = pd.read_csv(
    TRADES_FILE
)

profiles = pd.read_csv(
    PROFILE_FILE
)

trades["signal_time"] = pd.to_datetime(
    trades["signal_time"],
    utc=True
)

trades["entry_time"] = pd.to_datetime(
    trades["entry_time"],
    utc=True
)

trades["exit_time"] = pd.to_datetime(
    trades["exit_time"],
    utc=True
)

trades["session_date"] = pd.to_datetime(
    trades["session_date"]
).dt.date

trades["profile_date"] = pd.to_datetime(
    trades["profile_date"]
).dt.date

profiles["session_date"] = pd.to_datetime(
    profiles["session_date"]
).dt.date

profiles["profile_date"] = pd.to_datetime(
    profiles["profile_date"]
).dt.date


# ============================================================
# 1. OOS DATE CHECK
# ============================================================

oos_check = (
    (trades["session_date"] >= OOS_START)
    &
    (trades["session_date"] <= OOS_END)
)

print()
print("1. OOS DATE CHECK")
print("-" * 80)

print(
    f"Trades inside OOS period : "
    f"{oos_check.sum()}/{len(trades)}"
)

print(
    "PASS"
    if oos_check.all()
    else "FAIL"
)


# ============================================================
# 2. PROFILE CAUSALITY
# ============================================================

profile_check = (
    trades["profile_date"]
    <
    trades["session_date"]
)

print()
print("2. PROFILE CAUSALITY")
print("-" * 80)

print(
    f"Profile before session : "
    f"{profile_check.sum()}/{len(trades)}"
)

print(
    "PASS"
    if profile_check.all()
    else "FAIL"
)


# ============================================================
# 3. ENTRY AFTER SIGNAL
# ============================================================

entry_after_signal = (
    trades["entry_time"]
    >
    trades["signal_time"]
)

print()
print("3. ENTRY AFTER SIGNAL")
print("-" * 80)

print(
    f"Valid entries : "
    f"{entry_after_signal.sum()}/{len(trades)}"
)

print(
    "PASS"
    if entry_after_signal.all()
    else "FAIL"
)


# ============================================================
# 4. ENTRY DELAY
# ============================================================

delay_minutes = (
    trades["entry_time"]
    -
    trades["signal_time"]
).dt.total_seconds() / 60

print()
print("4. ENTRY DELAY")
print("-" * 80)

print(
    f"Min delay  : {delay_minutes.min():.2f} min"
)

print(
    f"Max delay  : {delay_minutes.max():.2f} min"
)

print(
    f"Mean delay : {delay_minutes.mean():.2f} min"
)

delay_check = (
    delay_minutes == 5
)

print(
    "PASS"
    if delay_check.all()
    else "FAIL"
)


# ============================================================
# 5. ONE TRADE PER SESSION
# ============================================================

session_counts = (
    trades
    .groupby(
        ["session_date", "session"]
    )
    .size()
)

one_trade_check = (
    session_counts <= 1
)

print()
print("5. ONE TRADE PER SESSION")
print("-" * 80)

print(
    f"Sessions with >1 trade : "
    f"{(~one_trade_check).sum()}"
)

print(
    "PASS"
    if one_trade_check.all()
    else "FAIL"
)


# ============================================================
# 6. RR CHECK
# ============================================================

buy_trades = trades[
    trades["direction"] == "BUY"
].copy()

sell_trades = trades[
    trades["direction"] == "SELL"
].copy()


buy_risk = (
    buy_trades["entry"]
    -
    buy_trades["sl"]
)

buy_reward = (
    buy_trades["tp"]
    -
    buy_trades["entry"]
)

sell_risk = (
    sell_trades["sl"]
    -
    sell_trades["entry"]
)

sell_reward = (
    sell_trades["entry"]
    -
    sell_trades["tp"]
)

buy_rr = (
    buy_reward / buy_risk
)

sell_rr = (
    sell_reward / sell_risk
)

all_rr = pd.concat(
    [
        buy_rr,
        sell_rr
    ],
    ignore_index=True
)

rr_check = (
    (all_rr - 2.0).abs()
    < 1e-9
)

print()
print("6. RR CHECK")
print("-" * 80)

print(
    f"RR min  : {all_rr.min():.3f}"
)

print(
    f"RR max  : {all_rr.max():.3f}"
)

print(
    f"RR mean : {all_rr.mean():.3f}"
)

print(
    "PASS"
    if rr_check.all()
    else "FAIL"
)


# ============================================================
# 7. EXIT AFTER ENTRY
# ============================================================

exit_after_entry = (
    trades["exit_time"]
    >=
    trades["entry_time"]
)

print()
print("7. EXIT AFTER ENTRY")
print("-" * 80)

print(
    f"Valid exits : "
    f"{exit_after_entry.sum()}/{len(trades)}"
)

print(
    "PASS"
    if exit_after_entry.all()
    else "FAIL"
)


# ============================================================
# 8. PNL CONSISTENCY
# ============================================================

def calculate_pnl(row):

    if row["direction"] == "BUY":

        risk = (
            row["entry"]
            -
            row["sl"]
        )

        return (
            row["exit"]
            -
            row["entry"]
        ) / risk

    else:

        risk = (
            row["sl"]
            -
            row["entry"]
        )

        return (
            row["entry"]
            -
            row["exit"]
        ) / risk


calculated_pnl = trades.apply(
    calculate_pnl,
    axis=1
)

pnl_difference = (
    calculated_pnl
    -
    trades["pnl_R"]
).abs()

pnl_check = (
    pnl_difference < 1e-9
)

print()
print("8. PNL CONSISTENCY")
print("-" * 80)

print(
    f"Max PnL difference : "
    f"{pnl_difference.max():.12f}"
)

print(
    "PASS"
    if pnl_check.all()
    else "FAIL"
)


# ============================================================
# 9. VALID EXIT REASONS
# ============================================================

valid_exit_reasons = {
    "SL",
    "TP",
    "TIME"
}

exit_reason_check = (
    trades["exit_reason"]
    .isin(valid_exit_reasons)
)

print()
print("9. EXIT REASON CHECK")
print("-" * 80)

print(
    f"Valid exit reasons : "
    f"{exit_reason_check.sum()}/{len(trades)}"
)

print(
    "PASS"
    if exit_reason_check.all()
    else "FAIL"
)


# ============================================================
# 10. TRADE COUNT
# ============================================================

print()
print("10. TRADE COUNT")
print("-" * 80)

print(
    f"Total OOS trades : {len(trades)}"
)

print(
    "PASS"
    if len(trades) > 0
    else "FAIL"
)


# ============================================================
# FINAL
# ============================================================

all_checks = [
    oos_check.all(),
    profile_check.all(),
    entry_after_signal.all(),
    delay_check.all(),
    one_trade_check.all(),
    rr_check.all(),
    exit_after_entry.all(),
    pnl_check.all(),
    exit_reason_check.all(),
    len(trades) > 0,
]

print()
print("=" * 80)

if all(all_checks):

    print("V4 OOS STRUCTURAL VALIDATION: PASSED")
    print()
    print("All structural validation checks passed.")

else:

    print("V4 OOS STRUCTURAL VALIDATION: FAILED")

    print()
    print("One or more validation checks failed.")

print("=" * 80)