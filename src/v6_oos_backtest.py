from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

MARKET_FILE = ROOT / "data" / "XAUUSD_M5.csv"
PROFILES_FILE = ROOT / "data" / "session_profiles_v2.csv"
OUTPUT_FILE = ROOT / "data" / "trades_v6_oos.csv"


# ============================================================
# CONFIG
# ============================================================

OOS_START = pd.Timestamp(
    "2025-09-12",
    tz="UTC"
)

OOS_END = pd.Timestamp(
    "2026-09-12",
    tz="UTC"
)

RR = 2.0

LEVEL_TOLERANCE = 0.50

SWING_LOOKBACK = 3

MIN_SL_DISTANCE = 0.30

MAX_SL_DISTANCE = 15.0

MAX_EXIT_CANDLES = 300

BODY_RATIO_MIN = 0.70

TIMEZONE = "Asia/Kolkata"


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(MARKET_FILE)

profiles = pd.read_csv(PROFILES_FILE)

print("=" * 70)
print("V6 OUT-OF-SAMPLE BACKTEST")
print("=" * 70)


# ============================================================
# MARKET DATA
# ============================================================

df["time"] = pd.to_datetime(
    df["time"],
    utc=True
)

df = df.sort_values(
    "time"
).reset_index(
    drop=True
)


# ============================================================
# PROFILE DATA
# ============================================================

profiles["session_date"] = pd.to_datetime(
    profiles["session_date"]
).dt.date

profiles["profile_date"] = pd.to_datetime(
    profiles["profile_date"]
).dt.date


# ============================================================
# OOS MARKET DATA
# ============================================================

oos_df = df[
    (df["time"] >= OOS_START)
    & (df["time"] < OOS_END)
].copy()


print(
    f"OOS period : "
    f"{OOS_START.date()} -> "
    f"{(OOS_END - pd.Timedelta(days=1)).date()}"
)

print(
    f"OOS candles: {len(oos_df)}"
)


# ============================================================
# IST SESSION INFORMATION
# ============================================================

oos_df["time_ist"] = (
    oos_df["time"]
    .dt.tz_convert(TIMEZONE)
)


oos_df["session_date"] = (
    oos_df["time_ist"]
    .dt.date
)


oos_df["weekday"] = (
    oos_df["time_ist"]
    .dt.weekday
)


# ============================================================
# SESSION CLASSIFICATION
# ============================================================

def get_session(row):

    if row["weekday"] >= 5:
        return None

    t = row["time_ist"].time()

    if (
        t >= pd.Timestamp("03:30").time()
        and
        t < pd.Timestamp("06:00").time()
    ):
        return "MORNING"

    if (
        t >= pd.Timestamp("18:55").time()
        and
        t < pd.Timestamp("19:55").time()
    ):
        return "US_OPEN"

    return None


oos_df["session"] = oos_df.apply(
    get_session,
    axis=1
)


session_df = oos_df[
    oos_df["session"].notna()
].copy()


print(
    f"OOS session candles: "
    f"{len(session_df)}"
)


# ============================================================
# PROFILE LOOKUP
# ============================================================

profile_lookup = {}

for _, row in profiles.iterrows():

    key = (
        row["session_date"],
        row["session"]
    )

    profile_lookup[key] = {
        "profile_date": row["profile_date"],
        "POC": float(row["POC"]),
        "VAH": float(row["VAH"]),
        "VAL": float(row["VAL"])
    }


# ============================================================
# BACKTEST
# ============================================================

trades = []

used_sessions = set()


# Use the complete chronological OOS dataset.
# Signal is evaluated on candle i.
# Entry occurs on candle i+1 open.
# Therefore the signal candle itself cannot be the entry candle.

for i in range(
    SWING_LOOKBACK,
    len(oos_df) - 1
):

    row = oos_df.iloc[i]

    session = row["session"]

    if pd.isna(session):
        continue


    session_date = row["session_date"]

    session_key = (
        session_date,
        session
    )


    # --------------------------------------------------------
    # ONE TRADE PER SESSION
    # --------------------------------------------------------

    if session_key in used_sessions:
        continue


    # --------------------------------------------------------
    # PROFILE
    # --------------------------------------------------------

    profile = profile_lookup.get(
        session_key
    )

    if profile is None:
        continue


    # --------------------------------------------------------
    # CAUSAL PROFILE CHECK
    # --------------------------------------------------------

    profile_date = profile["profile_date"]

    if profile_date >= session_date:
        continue


    # --------------------------------------------------------
    # CURRENT CANDLE
    # --------------------------------------------------------

    current_open = float(row["open"])

    current_high = float(row["high"])

    current_low = float(row["low"])

    current_close = float(row["close"])


    candle_range = (
        current_high
        - current_low
    )


    if candle_range <= 0:
        continue


    body_ratio = (
        abs(
            current_close
            - current_open
        )
        / candle_range
    )


    # --------------------------------------------------------
    # V5 BODY FILTER
    # --------------------------------------------------------

    if body_ratio < BODY_RATIO_MIN:
        continue


    # --------------------------------------------------------
    # PREVIOUS CLOSE
    # --------------------------------------------------------

    previous_close = float(
        oos_df.iloc[i - 1]["close"]
    )


    # --------------------------------------------------------
    # LEVELS
    # --------------------------------------------------------

    levels = {
        "POC": profile["POC"],
        "VAH": profile["VAH"],
        "VAL": profile["VAL"]
    }


    signal_found = False


    # ========================================================
    # BUY SIGNAL
    # ========================================================

    for level_name, level_price in levels.items():

        if (
            current_low
            <= level_price + LEVEL_TOLERANCE
            and
            current_close > level_price
            and
            previous_close <= level_price
        ):

            direction = "BUY"

            signal_found = True

            selected_level = level_name

            selected_level_price = level_price

            break


    # ========================================================
    # SELL SIGNAL
    # ========================================================

    if not signal_found:

        for level_name, level_price in levels.items():

            if (
                current_high
                >= level_price - LEVEL_TOLERANCE
                and
                current_close < level_price
                and
                previous_close >= level_price
            ):

                direction = "SELL"

                signal_found = True

                selected_level = level_name

                selected_level_price = level_price

                break


    if not signal_found:
        continue


    # ========================================================
    # ENTRY CANDLE
    # ========================================================

    entry_row = oos_df.iloc[i + 1]

    entry_time = entry_row["time"]

    entry_price = float(
        entry_row["open"]
    )


    # ========================================================
    # SWING STOP
    # ========================================================

    swing_window = oos_df.iloc[
        i - SWING_LOOKBACK:i + 1
    ]


    if direction == "BUY":

        sl_price = float(
            swing_window["low"].min()
        )

        risk = (
            entry_price
            - sl_price
        )

        if (
            risk < MIN_SL_DISTANCE
            or
            risk > MAX_SL_DISTANCE
        ):
            continue

        tp_price = (
            entry_price
            + RR * risk
        )


    else:

        sl_price = float(
            swing_window["high"].max()
        )

        risk = (
            sl_price
            - entry_price
        )

        if (
            risk < MIN_SL_DISTANCE
            or
            risk > MAX_SL_DISTANCE
        ):
            continue

        tp_price = (
            entry_price
            - RR * risk
        )


    # ========================================================
    # EXIT SEARCH
    # ========================================================

    exit_found = False

    exit_price = np.nan

    exit_reason = None

    exit_time = None


    exit_end = min(
        i + 1 + MAX_EXIT_CANDLES,
        len(oos_df)
    )


    for j in range(
        i + 1,
        exit_end
    ):

        exit_row = oos_df.iloc[j]

        high = float(
            exit_row["high"]
        )

        low = float(
            exit_row["low"]
        )


        if direction == "BUY":

            sl_hit = (
                low <= sl_price
            )

            tp_hit = (
                high >= tp_price
            )


            # Conservative assumption:
            # if SL and TP occur on same candle,
            # SL is considered first.

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

            sl_hit = (
                high >= sl_price
            )

            tp_hit = (
                low <= tp_price
            )


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


    # ========================================================
    # NO EXIT
    # ========================================================

    if not exit_found:
        continue


    # ========================================================
    # R MULTIPLE
    # ========================================================

    if direction == "BUY":

        pnl_r = (
            exit_price
            - entry_price
        ) / risk

    else:

        pnl_r = (
            entry_price
            - exit_price
        ) / risk


    # ========================================================
    # STORE TRADE
    # ========================================================

    trades.append(
        {
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

            "body_ratio": body_ratio
        }
    )


    used_sessions.add(
        session_key
    )


# ============================================================
# SAVE RESULTS
# ============================================================

trades_df = pd.DataFrame(
    trades
)


if len(trades_df) == 0:

    print()
    print(
        "NO OOS TRADES GENERATED."
    )

    raise SystemExit


trades_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# PERFORMANCE
# ============================================================

total_trades = len(
    trades_df
)

winners = (
    trades_df["pnl_R"] > 0
).sum()

losers = (
    trades_df["pnl_R"] < 0
).sum()


win_rate = (
    winners
    / total_trades
    * 100
)


gross_profit = (
    trades_df.loc[
        trades_df["pnl_R"] > 0,
        "pnl_R"
    ].sum()
)


gross_loss = abs(
    trades_df.loc[
        trades_df["pnl_R"] < 0,
        "pnl_R"
    ].sum()
)


profit_factor = (
    gross_profit
    / gross_loss
    if gross_loss > 0
    else np.inf
)


total_r = (
    trades_df["pnl_R"]
    .sum()
)


expectancy = (
    trades_df["pnl_R"]
    .mean()
)


equity = (
    trades_df["pnl_R"]
    .cumsum()
)

drawdown = (
    equity
    - equity.cummax()
)

max_drawdown = (
    drawdown.min()
)


# ============================================================
# MAX LOSS STREAK
# ============================================================

loss_flags = (
    trades_df["pnl_R"] < 0
).astype(int)

max_loss_streak = 0

current_streak = 0

for value in loss_flags:

    if value == 1:

        current_streak += 1

        max_loss_streak = max(
            max_loss_streak,
            current_streak
        )

    else:

        current_streak = 0


# ============================================================
# REPORT
# ============================================================

print()
print("=" * 70)
print("V6 OUT-OF-SAMPLE BACKTEST RESULT")
print("=" * 70)

print(
    f"OOS PERIOD       : "
    f"{OOS_START.date()} -> "
    f"{(OOS_END - pd.Timedelta(days=1)).date()}"
)

print(
    f"Total Trades     : {total_trades}"
)

print(
    f"Winners          : {winners}"
)

print(
    f"Losers           : {losers}"
)

print(
    f"Win Rate         : {win_rate:.2f}%"
)

print(
    f"Profit Factor    : {profit_factor:.2f}"
)

print(
    f"Total R          : {total_r:.2f}R"
)

print(
    f"Expectancy       : {expectancy:.3f}R"
)

print(
    f"Max Drawdown     : {max_drawdown:.2f}R"
)

print(
    f"Max Loss Streak  : {max_loss_streak}"
)


# ============================================================
# SESSION BREAKDOWN
# ============================================================

print()
print("SESSION BREAKDOWN")
print("-" * 70)

for session_name in [
    "MORNING",
    "US_OPEN"
]:

    subset = trades_df[
        trades_df["session"]
        == session_name
    ]

    if len(subset) == 0:
        continue

    print(
        f"{session_name:10} "
        f"{len(subset):4} trades | "
        f"{subset['pnl_R'].sum():7.2f}R | "
        f"mean "
        f"{subset['pnl_R'].mean():.3f}R"
    )


# ============================================================
# DIRECTION BREAKDOWN
# ============================================================

print()
print("DIRECTION BREAKDOWN")
print("-" * 70)

for direction_name in [
    "BUY",
    "SELL"
]:

    subset = trades_df[
        trades_df["direction"]
        == direction_name
    ]

    if len(subset) == 0:
        continue

    print(
        f"{direction_name:10} "
        f"{len(subset):4} trades | "
        f"{subset['pnl_R'].sum():7.2f}R | "
        f"mean "
        f"{subset['pnl_R'].mean():.3f}R"
    )


# ============================================================
# LEVEL BREAKDOWN
# ============================================================

print()
print("LEVEL BREAKDOWN")
print("-" * 70)

for level_name in [
    "POC",
    "VAH",
    "VAL"
]:

    subset = trades_df[
        trades_df["level"]
        == level_name
    ]

    if len(subset) == 0:
        continue

    print(
        f"{level_name:10} "
        f"{len(subset):4} trades | "
        f"{subset['pnl_R'].sum():7.2f}R | "
        f"mean "
        f"{subset['pnl_R'].mean():.3f}R"
    )


# ============================================================
# EXIT BREAKDOWN
# ============================================================

print()
print("EXIT BREAKDOWN")
print("-" * 70)

for exit_name in [
    "SL",
    "TP",
    "TIME"
]:

    subset = trades_df[
        trades_df["exit_reason"]
        == exit_name
    ]

    if len(subset) == 0:
        continue

    print(
        f"{exit_name:10} "
        f"{len(subset):4} trades | "
        f"{subset['pnl_R'].sum():7.2f}R"
    )


# ============================================================
# BODY RATIO
# ============================================================

print()
print("BODY RATIO")
print("-" * 70)

print(
    f"Min    : "
    f"{trades_df['body_ratio'].min():.6f}"
)

print(
    f"Mean   : "
    f"{trades_df['body_ratio'].mean():.6f}"
)

print(
    f"Max    : "
    f"{trades_df['body_ratio'].max():.6f}"
)


print()
print(
    f"Saved OOS trades -> "
    f"{OUTPUT_FILE}"
)

print("=" * 70)
