from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

TRADES_FILE = ROOT / "data" / "trades_v5.csv"
PROFILES_FILE = ROOT / "data" / "session_profiles_v2.csv"
MARKET_FILE = ROOT / "data" / "XAUUSD_M5.csv"


# ============================================================
# LOAD DATA
# ============================================================

trades = pd.read_csv(TRADES_FILE)
profiles = pd.read_csv(PROFILES_FILE)
market = pd.read_csv(MARKET_FILE)

print("=" * 70)
print("V5 STRUCTURAL VALIDATION")
print("=" * 70)

print(f"Trades   : {len(trades)}")
print(f"Profiles : {len(profiles)}")
print(f"Market   : {len(market)}")


# ============================================================
# DATE / TIME NORMALIZATION
# ============================================================

trades["session_date"] = pd.to_datetime(
    trades["session_date"]
).dt.date

trades["profile_date"] = pd.to_datetime(
    trades["profile_date"]
).dt.date

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

profiles["session_date"] = pd.to_datetime(
    profiles["session_date"]
).dt.date

profiles["profile_date"] = pd.to_datetime(
    profiles["profile_date"]
).dt.date

market["time"] = pd.to_datetime(
    market["time"],
    utc=True
)


# ============================================================
# VALIDATION HELPER
# ============================================================

results = {}


def check(name, condition):

    results[name] = bool(condition)

    status = "PASS" if condition else "FAIL"

    print(f"[{status}] {name}")


# ============================================================
# 1. TRADE COUNT
# ============================================================

check(
    "trade_count_positive",
    len(trades) > 0
)


# ============================================================
# 2. PROFILE CAUSALITY
# ============================================================

check(
    "profile_before_session",
    (
        trades["profile_date"]
        < trades["session_date"]
    ).all()
)

check(
    "all_profiles_found",
    trades["profile_date"].notna().all()
)

print(
    f"Valid previous profiles: "
    f"{trades['profile_date'].notna().sum()}/{len(trades)}"
)


# ============================================================
# 3. ENTRY MUST HAPPEN AFTER SIGNAL
# ============================================================

entry_delay = (
    trades["entry_time"]
    - trades["signal_time"]
).dt.total_seconds() / 60

check(
    "entry_after_signal",
    (entry_delay > 0).all()
)

print(
    f"Entry delay min/max/mean: "
    f"{entry_delay.min():.2f} / "
    f"{entry_delay.max():.2f} / "
    f"{entry_delay.mean():.2f} min"
)

check(
    "entry_delay_exactly_5min",
    np.isclose(
        entry_delay,
        5.0,
        atol=1e-9
    ).all()
)


# ============================================================
# 4. ONE TRADE PER SESSION
# ============================================================

session_counts = (
    trades
    .groupby(
        [
            "session_date",
            "session"
        ]
    )
    .size()
)

duplicate_sessions = (
    session_counts > 1
).sum()

check(
    "one_trade_per_session",
    duplicate_sessions == 0
)

print(
    f"Sessions with >1 trade: "
    f"{duplicate_sessions}"
)


# ============================================================
# 5. TP MUST BE +2R
# ============================================================

tp_trades = trades[
    trades["exit_reason"]
    .astype(str)
    .str.upper()
    == "TP"
].copy()

tp_pnl = pd.to_numeric(
    tp_trades["pnl_R"],
    errors="coerce"
)

tp_rr_valid = np.isclose(
    tp_pnl,
    2.0,
    atol=1e-9
).all()

check(
    "tp_equals_2R",
    tp_rr_valid
)

print(
    f"TP trades: {len(tp_trades)}"
)


# ============================================================
# 6. SL MUST BE -1R
# ============================================================

sl_trades = trades[
    trades["exit_reason"]
    .astype(str)
    .str.upper()
    == "SL"
].copy()

sl_pnl = pd.to_numeric(
    sl_trades["pnl_R"],
    errors="coerce"
)

sl_rr_valid = np.isclose(
    sl_pnl,
    -1.0,
    atol=1e-9
).all()

check(
    "sl_equals_minus_1R",
    sl_rr_valid
)

print(
    f"SL trades: {len(sl_trades)}"
)


# ============================================================
# 7. EXIT MUST NOT OCCUR BEFORE ENTRY
# ============================================================

exit_delay = (
    trades["exit_time"]
    - trades["entry_time"]
).dt.total_seconds()

check(
    "exit_after_entry",
    (exit_delay >= 0).all()
)

same_candle_exits = (
    exit_delay == 0
).sum()

print(
    f"Same-candle exits: "
    f"{same_candle_exits}"
)


# ============================================================
# 8. VALID EXIT REASONS
# ============================================================

valid_exit_reasons = {
    "SL",
    "TP",
    "TIME"
}

actual_exit_reasons = set(
    trades["exit_reason"]
    .astype(str)
    .str.upper()
    .unique()
)

invalid_exit_reasons = (
    actual_exit_reasons
    - valid_exit_reasons
)

check(
    "valid_exit_reasons",
    len(invalid_exit_reasons) == 0
)

print(
    f"Exit reasons: "
    f"{sorted(actual_exit_reasons)}"
)


# ============================================================
# 9. PNL_R CONSISTENCY
# ============================================================

required_columns = {
    "entry",
    "sl",
    "exit",
    "direction",
    "pnl_R"
}

missing_columns = (
    required_columns
    - set(trades.columns)
)

if missing_columns:

    check(
        "pnl_consistency",
        False
    )

    print(
        f"Missing columns: "
        f"{missing_columns}"
    )

else:

    calculated_r = []

    for _, row in trades.iterrows():

        entry = float(
            row["entry"]
        )

        sl = float(
            row["sl"]
        )

        exit_price = float(
            row["exit"]
        )

        direction = str(
            row["direction"]
        ).upper()

        risk = abs(
            entry - sl
        )

        if risk <= 0:

            calculated_r.append(
                np.nan
            )

            continue

        if direction == "BUY":

            r_value = (
                exit_price - entry
            ) / risk

        elif direction == "SELL":

            r_value = (
                entry - exit_price
            ) / risk

        else:

            r_value = np.nan

        calculated_r.append(
            r_value
        )

    calculated_r = np.array(
        calculated_r,
        dtype=float
    )

    stored_r = pd.to_numeric(
        trades["pnl_R"],
        errors="coerce"
    ).to_numpy()

    valid_r = (
        ~np.isnan(calculated_r)
        & ~np.isnan(stored_r)
    )

    if valid_r.any():

        max_difference = np.max(
            np.abs(
                calculated_r[valid_r]
                - stored_r[valid_r]
            )
        )

    else:

        max_difference = np.inf

    print(
        f"Max R calculation difference: "
        f"{max_difference:.12f}"
    )

    check(
        "pnl_consistency",
        max_difference < 1e-9
    )


# ============================================================
# 10. V5 BODY-RATIO FILTER
# ============================================================

body_ratio = pd.to_numeric(
    trades["body_ratio"],
    errors="coerce"
)

check(
    "body_ratio_present",
    body_ratio.notna().all()
)

check(
    "body_ratio_filter_50pct",
    (body_ratio >= 0.50).all()
)

print(
    f"Body ratio min/max/mean: "
    f"{body_ratio.min():.6f} / "
    f"{body_ratio.max():.6f} / "
    f"{body_ratio.mean():.6f}"
)


# ============================================================
# 11. RECOMPUTE BODY RATIO FROM ORIGINAL MARKET DATA
# ============================================================

market_lookup = market.set_index(
    "time"
)

recomputed_ratios = []

for signal_time in trades["signal_time"]:

    if signal_time not in market_lookup.index:

        recomputed_ratios.append(
            np.nan
        )

        continue

    candle = market_lookup.loc[
        signal_time
    ]

    candle_open = float(
        candle["open"]
    )

    candle_high = float(
        candle["high"]
    )

    candle_low = float(
        candle["low"]
    )

    candle_close = float(
        candle["close"]
    )

    candle_range = (
        candle_high
        - candle_low
    )

    if candle_range <= 0:

        recomputed_ratios.append(
            np.nan
        )

        continue

    ratio = (
        abs(
            candle_close
            - candle_open
        )
        / candle_range
    )

    recomputed_ratios.append(
        ratio
    )

recomputed_ratios = np.array(
    recomputed_ratios,
    dtype=float
)

stored_ratios = body_ratio.to_numpy()

valid_body = (
    ~np.isnan(recomputed_ratios)
    & ~np.isnan(stored_ratios)
)

if valid_body.any():

    max_body_difference = np.max(
        np.abs(
            recomputed_ratios[valid_body]
            - stored_ratios[valid_body]
        )
    )

else:

    max_body_difference = np.inf

print(
    f"Body ratio calculation difference: "
    f"{max_body_difference:.12f}"
)

check(
    "body_ratio_calculation_consistent",
    valid_body.all()
    and max_body_difference < 1e-9
)


# ============================================================
# 12. STORED PROFILE DATE VALIDITY
# ============================================================

check(
    "stored_profile_date_valid",
    (
        trades["profile_date"]
        < trades["session_date"]
    ).all()
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 70)
print("FINAL VALIDATION SUMMARY")
print("=" * 70)

failed = [
    name
    for name, passed in results.items()
    if not passed
]

for name, passed in results.items():

    status = (
        "PASS"
        if passed
        else "FAIL"
    )

    print(
        f"{status:4} | {name}"
    )

print()

if not failed:

    print(
        "V5 STRUCTURAL VALIDATION: PASSED"
    )

    print(
        "All causal, execution, RR, PnL "
        "and body-ratio validation checks passed."
    )

else:

    print(
        "V5 STRUCTURAL VALIDATION: FAILED"
    )

    print(
        "Failed checks:"
    )

    for item in failed:

        print(
            f" - {item}"
        )

print("=" * 70)