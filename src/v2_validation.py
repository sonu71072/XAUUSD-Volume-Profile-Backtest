import pandas as pd
import re

TRADES_FILE = "data/trades_v2.csv"
PROFILES_FILE = "data/session_profiles_v2.csv"

TIMEZONE = "Asia/Kolkata"

print("=" * 80)
print("V2.4 — CAUSAL VALIDATION AUDIT")
print("=" * 80)


# ============================================================
# LOAD
# ============================================================

trades = pd.read_csv(TRADES_FILE)
profiles = pd.read_csv(PROFILES_FILE)

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


# ============================================================
# NORMALIZE TRADE SESSION DATE
# ============================================================

trades["session_date"] = pd.to_datetime(
    trades["session_date"],
    errors="coerce"
).dt.date


# ============================================================
# NORMALIZE PROFILE SESSION DATE
# ============================================================

profiles["session_date"] = pd.to_datetime(
    profiles["session_date"],
    errors="coerce"
).dt.date


# ============================================================
# CLEAN PROFILE DATE
# ============================================================

def clean_profile_date(value):

    text = str(value)

    # Old format:
    # (datetime.date(2024, 9, 17), 'US_OPEN')

    match = re.search(
        r"datetime\.date\((\d+),\s*(\d+),\s*(\d+)\)",
        text
    )

    if match:

        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))

        return pd.Timestamp(
            year,
            month,
            day
        ).date()

    parsed = pd.to_datetime(
        value,
        errors="coerce"
    )

    if pd.isna(parsed):
        return None

    return parsed.date()


profiles["profile_date_only"] = (
    profiles["profile_date"]
    .apply(clean_profile_date)
)


print(f"Trades   : {len(trades):,}")
print(f"Profiles : {len(profiles):,}")


# ============================================================
# 1. SIGNAL → ENTRY
# ============================================================

print("\n" + "=" * 80)
print("1. SIGNAL → ENTRY VALIDATION")
print("=" * 80)

delay = (
    trades["entry_time"]
    - trades["signal_time"]
).dt.total_seconds() / 60

print(f"Min delay : {delay.min():.2f} min")
print(f"Max delay : {delay.max():.2f} min")
print(f"Mean delay: {delay.mean():.2f} min")

entry_after_signal = (
    delay > 0
)

if entry_after_signal.all():

    print(
        "PASS: Every entry occurs after signal candle."
    )

else:

    print(
        "FAIL: Invalid entry timing detected."
    )


# ============================================================
# 2. PROFILE TEMPORAL VALIDATION
# ============================================================

print("\n" + "=" * 80)
print("2. PROFILE TEMPORAL VALIDATION")
print("=" * 80)


profile_check = profiles[
    [
        "session_date",
        "session",
        "profile_date_only"
    ]
].copy()


trades_check = trades.merge(
    profile_check,
    on=[
        "session_date",
        "session"
    ],
    how="left"
)


trades_check["signal_date"] = (
    trades_check["signal_time"]
    .dt.tz_convert(TIMEZONE)
    .dt.date
)


valid_profile_date = (
    trades_check["profile_date_only"].notna()
    &
    (
        trades_check["profile_date_only"]
        <
        trades_check["signal_date"]
    )
)


valid_count = int(
    valid_profile_date.sum()
)

total_count = len(
    trades_check
)

missing_count = int(
    trades_check["profile_date_only"]
    .isna()
    .sum()
)


print(
    f"Valid previous profiles: "
    f"{valid_count}/{total_count}"
)

print(
    f"Missing profile dates   : "
    f"{missing_count}"
)


if valid_profile_date.all():

    print(
        "PASS: Every trade uses a "
        "previous completed profile."
    )

else:

    print(
        "FAIL: Current/future/missing "
        "profile detected."
    )

    # Show first few problematic rows
    print("\nProblematic rows:")

    print(
        trades_check.loc[
            ~valid_profile_date,
            [
                "session_date",
                "session",
                "signal_date",
                "profile_date_only"
            ]
        ]
        .head(10)
        .to_string(index=False)
    )


# ============================================================
# 3. PROFILE UNIQUENESS
# ============================================================

print("\n" + "=" * 80)
print("3. PROFILE UNIQUENESS")
print("=" * 80)

profile_counts = (
    profiles
    .groupby(
        [
            "session_date",
            "session"
        ]
    )
    .size()
)

duplicates = profile_counts[
    profile_counts > 1
]

print(
    f"Duplicate session profiles: "
    f"{len(duplicates)}"
)

unique_profiles = (
    len(duplicates) == 0
)

if unique_profiles:

    print(
        "PASS: One profile per session."
    )

else:

    print(
        "FAIL: Duplicate profiles found."
    )


# ============================================================
# 4. ENTRY PRICE VALIDATION
# ============================================================

print("\n" + "=" * 80)
print("4. ENTRY PRICE VALIDATION")
print("=" * 80)

entry_valid = (
    trades["entry_time"]
    >
    trades["signal_time"]
)

print(
    f"Valid entries: "
    f"{entry_valid.sum()}/{len(trades)}"
)

if entry_valid.all():

    print(
        "PASS: All trades enter after "
        "signal candle close."
    )

else:

    print(
        "FAIL: Invalid entry timing found."
    )


# ============================================================
# 5. SL / TP VALIDATION
# ============================================================

print("\n" + "=" * 80)
print("5. SL / TP VALIDATION")
print("=" * 80)

buy = trades[
    trades["direction"] == "BUY"
]

sell = trades[
    trades["direction"] == "SELL"
]


buy_sl_valid = (
    buy["sl"] < buy["entry"]
)

buy_tp_valid = (
    buy["tp"] > buy["entry"]
)

sell_sl_valid = (
    sell["sl"] > sell["entry"]
)

sell_tp_valid = (
    sell["tp"] < sell["entry"]
)


print(
    f"BUY SL valid : "
    f"{buy_sl_valid.sum()}/{len(buy)}"
)

print(
    f"BUY TP valid : "
    f"{buy_tp_valid.sum()}/{len(buy)}"
)

print(
    f"SELL SL valid: "
    f"{sell_sl_valid.sum()}/{len(sell)}"
)

print(
    f"SELL TP valid: "
    f"{sell_tp_valid.sum()}/{len(sell)}"
)


sl_tp_valid = (
    buy_sl_valid.all()
    and buy_tp_valid.all()
    and sell_sl_valid.all()
    and sell_tp_valid.all()
)


if sl_tp_valid:

    print(
        "PASS: SL/TP directions are valid."
    )

else:

    print(
        "FAIL: Invalid SL/TP detected."
    )


# ============================================================
# 6. RISK / REWARD
# ============================================================

print("\n" + "=" * 80)
print("6. RISK / REWARD VALIDATION")
print("=" * 80)

buy_risk = (
    buy["entry"] -
    buy["sl"]
)

buy_reward = (
    buy["tp"] -
    buy["entry"]
)

sell_risk = (
    sell["sl"] -
    sell["entry"]
)

sell_reward = (
    sell["entry"] -
    sell["tp"]
)


buy_rr = (
    buy_reward /
    buy_risk
)

sell_rr = (
    sell_reward /
    sell_risk
)


all_rr = pd.concat(
    [
        buy_rr,
        sell_rr
    ],
    ignore_index=True
)


print(
    f"Minimum RR : {all_rr.min():.3f}"
)

print(
    f"Maximum RR : {all_rr.max():.3f}"
)

print(
    f"Mean RR    : {all_rr.mean():.3f}"
)


rr_valid = (
    (all_rr - 2.0).abs()
    < 1e-6
)


if rr_valid.all():

    print(
        "PASS: Every trade uses exactly 2R target."
    )

else:

    print(
        "FAIL: RR mismatch detected."
    )


# ============================================================
# 7. ONE TRADE PER SESSION
# ============================================================

print("\n" + "=" * 80)
print("7. ONE TRADE PER SESSION")
print("=" * 80)

session_trade_counts = (
    trades
    .groupby(
        [
            "session_date",
            "session"
        ]
    )
    .size()
)

violations = (
    session_trade_counts[
        session_trade_counts > 1
    ]
)

one_trade_valid = (
    len(violations) == 0
)

print(
    f"Sessions with >1 trade: "
    f"{len(violations)}"
)

if one_trade_valid:

    print(
        "PASS: Maximum one trade per session."
    )

else:

    print(
        "FAIL: Multiple trades detected."
    )


# ============================================================
# 8. EXIT TIMING
# ============================================================

print("\n" + "=" * 80)
print("8. EXIT TIMING")
print("=" * 80)

exit_valid = (
    trades["exit_time"]
    >=
    trades["entry_time"]
)

print(
    f"Valid exits: "
    f"{exit_valid.sum()}/{len(trades)}"
)

if exit_valid.all():

    print(
        "PASS: All exits occur at/after entry."
    )

else:

    print(
        "FAIL: Invalid exit timing found."
    )


# ============================================================
# 9. PNL CONSISTENCY
# ============================================================

print("\n" + "=" * 80)
print("9. PNL CONSISTENCY")
print("=" * 80)

calculated_r = []

for _, row in trades.iterrows():

    if row["direction"] == "BUY":

        risk = (
            row["entry"] -
            row["sl"]
        )

        calculated = (
            row["exit"] -
            row["entry"]
        ) / risk

    else:

        risk = (
            row["sl"] -
            row["entry"]
        )

        calculated = (
            row["entry"] -
            row["exit"]
        ) / risk

    calculated_r.append(
        calculated
    )


calculated_r = pd.Series(
    calculated_r,
    index=trades.index
)


difference = (
    calculated_r -
    trades["pnl_R"]
).abs()


pnl_valid = (
    difference.max()
    < 1e-6
)


print(
    "Maximum PnL calculation difference: "
    f"{difference.max():.8f}"
)

if pnl_valid:

    print(
        "PASS: Stored PnL matches "
        "price calculation."
    )

else:

    print(
        "FAIL: PnL mismatch detected."
    )


# ============================================================
# FINAL VALIDATION
# ============================================================

checks = {

    "entry_after_signal":
        entry_after_signal.all(),

    "profile_before_signal":
        valid_profile_date.all(),

    "sl_tp_valid":
        sl_tp_valid,

    "rr_valid":
        rr_valid.all(),

    "one_trade_per_session":
        one_trade_valid,

    "exit_after_entry":
        exit_valid.all(),

    "pnl_consistent":
        pnl_valid,

    "unique_profiles":
        unique_profiles,
}


print("\n" + "=" * 80)
print("FINAL VALIDATION")
print("=" * 80)

for name, result in checks.items():

    status = (
        "PASS"
        if result
        else
        "FAIL"
    )

    print(
        f"{status:5} : {name}"
    )


print("\n" + "=" * 80)

if all(checks.values()):

    print(
        "V2.2 CAUSAL VALIDATION: PASSED"
    )

    print(
        "All structural validation checks passed."
    )

else:

    print(
        "V2.2 CAUSAL VALIDATION: REQUIRES REVIEW"
    )

    print(
        "At least one structural check failed."
    )

print("=" * 80)