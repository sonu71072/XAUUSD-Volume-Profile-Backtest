from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

MARKET_FILE = ROOT / "data" / "XAUUSD_M5.csv"
PROFILES_FILE = ROOT / "data" / "session_profiles_v2.csv"
OUTPUT_FILE = ROOT / "data" / "trades_v8_oos.csv"

OOS_START = pd.Timestamp("2025-09-12", tz="UTC")
OOS_END = pd.Timestamp("2026-09-12", tz="UTC")

RR = 2.0
LEVEL_TOLERANCE = 0.50
SWING_LOOKBACK = 3
MIN_SL_DISTANCE = 0.30
MAX_SL_DISTANCE = 15.0
MAX_EXIT_CANDLES = 300
BODY_RATIO_MIN = 0.70
POC_DISTANCE_MAX_R = 0.20
TIMEZONE = "Asia/Kolkata"


def get_session(row):
    if row["weekday"] >= 5:
        return None

    t = row["time_ist"].time()

    if t >= pd.Timestamp("03:30").time() and t < pd.Timestamp("06:00").time():
        return "MORNING"

    if t >= pd.Timestamp("18:55").time() and t < pd.Timestamp("19:55").time():
        return "US_OPEN"

    return None


# ============================================================
# LOAD
# ============================================================

df = pd.read_csv(MARKET_FILE)
profiles = pd.read_csv(PROFILES_FILE)

df["time"] = pd.to_datetime(df["time"], utc=True)
df = df.sort_values("time").reset_index(drop=True)

profiles["session_date"] = pd.to_datetime(
    profiles["session_date"]
).dt.date

profiles["profile_date"] = pd.to_datetime(
    profiles["profile_date"]
).dt.date

print("=" * 70)
print("V8 OUT-OF-SAMPLE BACKTEST")
print("=" * 70)

# ============================================================
# OOS MARKET DATA — KEEP COMPLETE OOS DATASET
# ============================================================

oos_df = df[
    (df["time"] >= OOS_START) &
    (df["time"] < OOS_END)
].copy()

oos_df["time_ist"] = oos_df["time"].dt.tz_convert(TIMEZONE)
oos_df["session_date"] = oos_df["time_ist"].dt.date
oos_df["weekday"] = oos_df["time_ist"].dt.weekday
oos_df["session"] = oos_df.apply(get_session, axis=1)
oos_df = oos_df.reset_index(drop=True)

print(
    f"OOS period : {OOS_START.date()} -> "
    f"{(OOS_END - pd.Timedelta(days=1)).date()}"
)
print(f"OOS candles: {len(oos_df)}")
print(f"OOS session candles: {oos_df['session'].notna().sum()}")

# ============================================================
# PROFILE LOOKUP
# ============================================================

profile_lookup = {}

for _, p in profiles.iterrows():
    key = (p["session_date"], p["session"])
    profile_lookup[key] = {
        "profile_date": p["profile_date"],
        "POC": float(p["POC"]),
        "VAH": float(p["VAH"]),
        "VAL": float(p["VAL"]),
    }

# ============================================================
# BACKTEST
# ============================================================

trades = []
used_sessions = set()

signal_candidates = 0
distance_rejected = 0
distance_accepted = 0

for i in range(SWING_LOOKBACK, len(oos_df) - 1):

    row = oos_df.iloc[i]

    session = row["session"]

    if pd.isna(session):
        continue

    session_date = row["session_date"]
    session_key = (session_date, session)

    if session_key in used_sessions:
        continue

    profile = profile_lookup.get(session_key)

    if profile is None:
        continue

    # Causal profile check — same as V7 OOS.
    profile_date = profile["profile_date"]

    if profile_date >= session_date:
        continue

    current_open = float(row["open"])
    current_high = float(row["high"])
    current_low = float(row["low"])
    current_close = float(row["close"])

    candle_range = current_high - current_low

    if candle_range <= 0:
        continue

    body_ratio = abs(current_close - current_open) / candle_range

    if body_ratio < BODY_RATIO_MIN:
        continue

    previous_close = float(oos_df.iloc[i - 1]["close"])

    # V7 POC-only signal logic.
    poc = profile["POC"]

    signal_found = False

    if (
        current_low <= poc + LEVEL_TOLERANCE
        and current_close > poc
        and previous_close <= poc
    ):
        direction = "BUY"
        signal_found = True
        selected_level = "POC"
        selected_level_price = poc

    elif (
        current_high >= poc - LEVEL_TOLERANCE
        and current_close < poc
        and previous_close >= poc
    ):
        direction = "SELL"
        signal_found = True
        selected_level = "POC"
        selected_level_price = poc

    if not signal_found:
        continue

    signal_candidates += 1

    # ========================================================
    # ENTRY
    # ========================================================

    entry_row = oos_df.iloc[i + 1]
    entry_time = entry_row["time"]
    entry_price = float(entry_row["open"])

    # Same V7 swing window: includes signal candle.
    swing_window = oos_df.iloc[
        i - SWING_LOOKBACK:i + 1
    ]

    if direction == "BUY":

        sl_price = float(swing_window["low"].min())
        risk = entry_price - sl_price

        if risk < MIN_SL_DISTANCE or risk > MAX_SL_DISTANCE:
            continue

        tp_price = entry_price + RR * risk

    else:

        sl_price = float(swing_window["high"].max())
        risk = sl_price - entry_price

        if risk < MIN_SL_DISTANCE or risk > MAX_SL_DISTANCE:
            continue

        tp_price = entry_price - RR * risk

    # ========================================================
    # V8 FILTER — POC DISTANCE <= 0.20R
    # ========================================================

    poc_distance = abs(entry_price - selected_level_price)
    distance_risk = poc_distance / risk

    if distance_risk > POC_DISTANCE_MAX_R:
        distance_rejected += 1
        continue

    distance_accepted += 1

    # ========================================================
    # EXIT — SAME V7 OOS LOGIC
    # ========================================================

    exit_found = False
    exit_price = np.nan
    exit_reason = None
    exit_time = None

    exit_end = min(
        i + 1 + MAX_EXIT_CANDLES,
        len(oos_df)
    )

    for j in range(i + 1, exit_end):

        exit_row = oos_df.iloc[j]

        high = float(exit_row["high"])
        low = float(exit_row["low"])

        if direction == "BUY":

            sl_hit = low <= sl_price
            tp_hit = high >= tp_price

            # Conservative same-candle rule: SL first.
            if sl_hit:
                exit_price = sl_price
                exit_reason = "SL"
                exit_time = exit_row["time"]
                exit_found = True
                break

            if tp_hit:
                exit_price = tp_price
                exit_reason = "TP"
                exit_time = exit_row["time"]
                exit_found = True
                break

        else:

            sl_hit = high >= sl_price
            tp_hit = low <= tp_price

            if sl_hit:
                exit_price = sl_price
                exit_reason = "SL"
                exit_time = exit_row["time"]
                exit_found = True
                break

            if tp_hit:
                exit_price = tp_price
                exit_reason = "TP"
                exit_time = exit_row["time"]
                exit_found = True
                break

    if not exit_found:
        continue

    # ========================================================
    # PNL
    # ========================================================

    if direction == "BUY":
        pnl_r = (exit_price - entry_price) / risk
    else:
        pnl_r = (entry_price - exit_price) / risk

    trades.append({
        "signal_time": row["time"],
        "entry_time": entry_time,
        "exit_time": exit_time,
        "session_date": session_date,
        "session": session,
        "direction": direction,
        "level": selected_level,
        "level_price": selected_level_price,
        "profile_date": profile_date,
        "entry": entry_price,
        "sl": sl_price,
        "tp": tp_price,
        "exit": exit_price,
        "exit_reason": exit_reason,
        "pnl_R": pnl_r,
        "body_ratio": body_ratio,
        "poc_distance": poc_distance,
        "distance_risk": distance_risk,
    })

    used_sessions.add(session_key)

# ============================================================
# DIAGNOSTICS
# ============================================================

print()
print(f"Signal candidates : {signal_candidates}")
print(f"Distance rejected : {distance_rejected}")
print(f"Distance accepted : {distance_accepted}")

if not trades:
    print("\nNo V8 OOS trades generated.")
    raise SystemExit

# ============================================================
# SAVE
# ============================================================

trades_df = pd.DataFrame(trades)
trades_df.to_csv(OUTPUT_FILE, index=False)

# ============================================================
# PERFORMANCE
# ============================================================

total_trades = len(trades_df)
winners = int((trades_df["pnl_R"] > 0).sum())
losers = int((trades_df["pnl_R"] < 0).sum())

win_rate = winners / total_trades * 100

gross_profit = trades_df.loc[
    trades_df["pnl_R"] > 0, "pnl_R"
].sum()

gross_loss = abs(
    trades_df.loc[
        trades_df["pnl_R"] < 0, "pnl_R"
    ].sum()
)

profit_factor = (
    gross_profit / gross_loss
    if gross_loss > 0
    else np.inf
)

total_r = trades_df["pnl_R"].sum()
expectancy = trades_df["pnl_R"].mean()

equity = trades_df["pnl_R"].cumsum()
drawdown = equity - equity.cummax()
max_drawdown = drawdown.min()

max_loss_streak = 0
current_streak = 0

for value in trades_df["pnl_R"]:
    if value < 0:
        current_streak += 1
        max_loss_streak = max(max_loss_streak, current_streak)
    else:
        current_streak = 0

print()
print("=" * 70)
print("V8 OUT-OF-SAMPLE BACKTEST RESULT")
print("=" * 70)

print(
    f"OOS PERIOD       : "
    f"{OOS_START.date()} -> "
    f"{(OOS_END - pd.Timedelta(days=1)).date()}"
)
print(f"Total Trades     : {total_trades}")
print(f"Winners          : {winners}")
print(f"Losers           : {losers}")
print(f"Win Rate         : {win_rate:.2f}%")
print(f"Profit Factor    : {profit_factor:.2f}")
print(f"Total R          : {total_r:.2f}R")
print(f"Expectancy       : {expectancy:.3f}R")
print(f"Max Drawdown     : {max_drawdown:.2f}R")
print(f"Max Loss Streak  : {max_loss_streak}")

print()
print("SESSION BREAKDOWN")
print("-" * 70)
for name in ["MORNING", "US_OPEN"]:
    subset = trades_df[trades_df["session"] == name]
    if len(subset):
        print(
            f"{name:10} {len(subset):4} trades | "
            f"{subset['pnl_R'].sum():7.2f}R | "
            f"mean {subset['pnl_R'].mean():.3f}R"
        )

print()
print("DIRECTION BREAKDOWN")
print("-" * 70)
for name in ["BUY", "SELL"]:
    subset = trades_df[trades_df["direction"] == name]
    if len(subset):
        print(
            f"{name:10} {len(subset):4} trades | "
            f"{subset['pnl_R'].sum():7.2f}R | "
            f"mean {subset['pnl_R'].mean():.3f}R"
        )

print()
print("LEVEL BREAKDOWN")
print("-" * 70)
for name in ["POC"]:
    subset = trades_df[trades_df["level"] == name]
    if len(subset):
        print(
            f"{name:10} {len(subset):4} trades | "
            f"{subset['pnl_R'].sum():7.2f}R | "
            f"mean {subset['pnl_R'].mean():.3f}R"
        )

print()
print("EXIT BREAKDOWN")
print("-" * 70)
print(
    trades_df.groupby("exit_reason")["pnl_R"]
    .agg(["count", "sum"])
    .to_string()
)

print()
print("BODY RATIO")
print("-" * 70)
print(f"Min    : {trades_df['body_ratio'].min():.6f}")
print(f"Mean   : {trades_df['body_ratio'].mean():.6f}")
print(f"Max    : {trades_df['body_ratio'].max():.6f}")

print()
print("POC DISTANCE RISK")
print("-" * 70)
print(f"Max allowed : {POC_DISTANCE_MAX_R:.2f}R")
print(f"Min         : {trades_df['distance_risk'].min():.6f}")
print(f"Mean        : {trades_df['distance_risk'].mean():.6f}")
print(f"Max         : {trades_df['distance_risk'].max():.6f}")

print(f"\nSaved OOS trades -> {OUTPUT_FILE}")
print("=" * 70)
print("V8 OUT-OF-SAMPLE BACKTEST COMPLETE")
print("=" * 70)
