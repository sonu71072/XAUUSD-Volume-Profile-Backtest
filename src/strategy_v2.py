import pandas as pd
import numpy as np
import re

# ============================================================
# V2.2 — CAUSAL STRATEGY / NEXT-CANDLE EXECUTION
# ============================================================

DATA_FILE = "data/XAUUSD_M5.csv"
PROFILE_FILE = "data/session_profiles_v2.csv"
OUTPUT_FILE = "data/trades_v2.csv"

RR = 2.0

LEVEL_TOLERANCE = 0.50
SWING_LOOKBACK = 3

MIN_SL_DISTANCE = 0.30
MAX_SL_DISTANCE = 15.0

ONE_TRADE_PER_SESSION = True
MAX_EXIT_CANDLES = 300

TIMEZONE = "Asia/Kolkata"


# ============================================================
# PROFILE DATE CLEANER
# ============================================================

def clean_profile_date(value):
    """
    Convert profile_date into a clean YYYY-MM-DD string.

    Handles old tuple format such as:
    (datetime.date(2024, 9, 17), 'US_OPEN')
    """

    text = str(value).strip()

    match = re.search(
        r"datetime\.date\((\d+),\s*(\d+),\s*(\d+)\)",
        text
    )

    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))

        return f"{year:04d}-{month:02d}-{day:02d}"

    parsed = pd.to_datetime(
        value,
        errors="coerce"
    )

    if pd.isna(parsed):
        return None

    return parsed.strftime("%Y-%m-%d")


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 80)
print("V2.2 — CAUSAL STRATEGY / NEXT-CANDLE EXECUTION")
print("=" * 80)

df = pd.read_csv(
    DATA_FILE,
    parse_dates=["time"]
)

# IMPORTANT:
# Do NOT parse profile_date here because the CSV contains
# old tuple-like strings.
profiles = pd.read_csv(
    PROFILE_FILE
)

df = df.sort_values(
    "time"
).reset_index(drop=True)

profiles = profiles.sort_values(
    "session_date"
).reset_index(drop=True)


# ============================================================
# CLEAN PROFILE DATES
# ============================================================

profiles["session_date"] = pd.to_datetime(
    profiles["session_date"],
    errors="coerce"
)

profiles["profile_date"] = (
    profiles["profile_date"]
    .apply(clean_profile_date)
)

print(
    f"Loaded candles : {len(df):,}"
)

print(
    f"Loaded profiles: {len(profiles):,}"
)


# ============================================================
# VALIDATE PROFILE DATES
# ============================================================

missing_profile_dates = (
    profiles["profile_date"].isna()
).sum()

if missing_profile_dates > 0:

    print()
    print(
        f"WARNING: {missing_profile_dates} "
        "profiles have invalid profile dates."
    )


# ============================================================
# SESSION ASSIGNMENT
# ============================================================

def get_session(timestamp):

    ts = timestamp.tz_convert(
        TIMEZONE
    )

    if ts.weekday() >= 5:
        return None

    minutes = (
        ts.hour * 60
        + ts.minute
    )

    # --------------------------------------------------------
    # MORNING
    # 03:30 - 06:00 IST
    # --------------------------------------------------------

    if (
        3 * 60 + 30
        <= minutes
        < 6 * 60
    ):
        return "MORNING"

    # --------------------------------------------------------
    # US OPEN
    # 18:55 - 19:55 IST
    # --------------------------------------------------------

    if (
        18 * 60 + 55
        <= minutes
        < 19 * 60 + 55
    ):
        return "US_OPEN"

    return None


# ============================================================
# PREPARE CANDLE DATA
# ============================================================

if df["time"].dt.tz is None:

    df["time"] = (
        df["time"]
        .dt.tz_localize("UTC")
    )

df["session"] = (
    df["time"]
    .apply(get_session)
)

df["session_date"] = (
    df["time"]
    .dt.tz_convert(TIMEZONE)
    .dt.date
)


# ============================================================
# PREPARE PROFILE LOOKUP
# ============================================================

profile_lookup = {}

for _, row in profiles.iterrows():

    session_date = (
        row["session_date"].date()
    )

    session = row["session"]

    key = (
        session_date,
        session
    )

    profile_date_value = row["profile_date"]

    if pd.isna(profile_date_value):
        profile_date = None
    else:
        profile_date = pd.Timestamp(
            profile_date_value
        ).date()

    profile_lookup[key] = {

        "POC": float(
            row["POC"]
        ),

        "VAH": float(
            row["VAH"]
        ),

        "VAL": float(
            row["VAL"]
        ),

        "profile_date": profile_date,
    }


# ============================================================
# TRADE STORAGE
# ============================================================

trades = []

used_sessions = set()


# ============================================================
# MAIN BACKTEST
# ============================================================

for i in range(
    SWING_LOOKBACK + 2,
    len(df) - 1
):

    row = df.iloc[i]

    session = row["session"]

    if session is None:
        continue

    session_date = row["session_date"]

    session_key = (
        session_date,
        session
    )

    # --------------------------------------------------------
    # ONE TRADE PER SESSION
    # --------------------------------------------------------

    if (
        ONE_TRADE_PER_SESSION
        and session_key in used_sessions
    ):
        continue

    # --------------------------------------------------------
    # GET CAUSAL PROFILE
    # --------------------------------------------------------

    profile = profile_lookup.get(
        session_key
    )

    if profile is None:
        continue

    profile_date = profile[
        "profile_date"
    ]

    # --------------------------------------------------------
    # HARD CAUSALITY CHECK
    # --------------------------------------------------------

    if profile_date is None:
        continue

    if profile_date >= session_date:
        continue

    poc = profile["POC"]
    vah = profile["VAH"]
    val = profile["VAL"]

    # --------------------------------------------------------
    # SIGNAL CANDLE
    # --------------------------------------------------------

    current_low = float(
        row["low"]
    )

    current_high = float(
        row["high"]
    )

    current_close = float(
        row["close"]
    )

    previous_close = float(
        df.iloc[i - 1]["close"]
    )

    # --------------------------------------------------------
    # NEXT CANDLE
    # --------------------------------------------------------

    next_row = df.iloc[i + 1]

    next_open = float(
        next_row["open"]
    )


    # ========================================================
    # BUY SIGNAL
    # ========================================================

    buy_level = None

    for level_name, level in [
        ("POC", poc),
        ("VAH", vah),
        ("VAL", val),
    ]:

        if (
            current_low
            <= level + LEVEL_TOLERANCE
            and current_close > level
            and previous_close <= level
        ):

            buy_level = (
                level_name,
                level
            )

            break


    # ========================================================
    # SELL SIGNAL
    # ========================================================

    sell_level = None

    for level_name, level in [
        ("POC", poc),
        ("VAH", vah),
        ("VAL", val),
    ]:

        if (
            current_high
            >= level - LEVEL_TOLERANCE
            and current_close < level
            and previous_close >= level
        ):

            sell_level = (
                level_name,
                level
            )

            break


    # ========================================================
    # BUY
    # ========================================================

    if buy_level is not None:

        level_name, level = buy_level

        entry = next_open

        recent_low = (
            df.iloc[
                i - SWING_LOOKBACK:i + 1
            ]["low"]
            .min()
        )

        sl = float(
            recent_low
        )

        risk = (
            entry - sl
        )

        if (
            risk >= MIN_SL_DISTANCE
            and risk <= MAX_SL_DISTANCE
        ):

            tp = (
                entry
                + RR * risk
            )

            exit_price = None
            exit_reason = None
            exit_index = None

            max_index = min(
                i + 1 + MAX_EXIT_CANDLES,
                len(df) - 1
            )

            for j in range(
                i + 1,
                max_index + 1
            ):

                candle = df.iloc[j]

                candle_low = float(
                    candle["low"]
                )

                candle_high = float(
                    candle["high"]
                )

                # SL first
                if candle_low <= sl:

                    exit_price = sl
                    exit_reason = "SL"
                    exit_index = j

                    break

                if candle_high >= tp:

                    exit_price = tp
                    exit_reason = "TP"
                    exit_index = j

                    break

            if exit_price is None:

                exit_index = max_index

                exit_price = float(
                    df.iloc[
                        exit_index
                    ]["close"]
                )

                exit_reason = "TIME"

            pnl_r = (
                exit_price - entry
            ) / risk

            trades.append({

                "signal_time":
                    row["time"],

                "entry_time":
                    next_row["time"],

                "exit_time":
                    df.iloc[
                        exit_index
                    ]["time"],

                "session_date":
                    session_date,

                "session":
                    session,

                "direction":
                    "BUY",

                "level":
                    level_name,

                "level_price":
                    level,

                "profile_date":
                    profile_date,

                "entry":
                    entry,

                "sl":
                    sl,

                "tp":
                    tp,

                "exit":
                    exit_price,

                "exit_reason":
                    exit_reason,

                "pnl_R":
                    pnl_r,
            })

            used_sessions.add(
                session_key
            )

            continue


    # ========================================================
    # SELL
    # ========================================================

    if sell_level is not None:

        level_name, level = sell_level

        entry = next_open

        recent_high = (
            df.iloc[
                i - SWING_LOOKBACK:i + 1
            ]["high"]
            .max()
        )

        sl = float(
            recent_high
        )

        risk = (
            sl - entry
        )

        if (
            risk >= MIN_SL_DISTANCE
            and risk <= MAX_SL_DISTANCE
        ):

            tp = (
                entry
                - RR * risk
            )

            exit_price = None
            exit_reason = None
            exit_index = None

            max_index = min(
                i + 1 + MAX_EXIT_CANDLES,
                len(df) - 1
            )

            for j in range(
                i + 1,
                max_index + 1
            ):

                candle = df.iloc[j]

                candle_low = float(
                    candle["low"]
                )

                candle_high = float(
                    candle["high"]
                )

                # SL first
                if candle_high >= sl:

                    exit_price = sl
                    exit_reason = "SL"
                    exit_index = j

                    break

                if candle_low <= tp:

                    exit_price = tp
                    exit_reason = "TP"
                    exit_index = j

                    break

            if exit_price is None:

                exit_index = max_index

                exit_price = float(
                    df.iloc[
                        exit_index
                    ]["close"]
                )

                exit_reason = "TIME"

            pnl_r = (
                entry - exit_price
            ) / risk

            trades.append({

                "signal_time":
                    row["time"],

                "entry_time":
                    next_row["time"],

                "exit_time":
                    df.iloc[
                        exit_index
                    ]["time"],

                "session_date":
                    session_date,

                "session":
                    session,

                "direction":
                    "SELL",

                "level":
                    level_name,

                "level_price":
                    level,

                "profile_date":
                    profile_date,

                "entry":
                    entry,

                "sl":
                    sl,

                "tp":
                    tp,

                "exit":
                    exit_price,

                "exit_reason":
                    exit_reason,

                "pnl_R":
                    pnl_r,
            })

            used_sessions.add(
                session_key
            )


# ============================================================
# RESULTS
# ============================================================

trades_df = pd.DataFrame(
    trades
)

if trades_df.empty:

    print()
    print("NO TRADES GENERATED.")
    print("=" * 80)

else:

    # --------------------------------------------------------
    # FORCE CLEAN DATE FORMAT
    # --------------------------------------------------------

    trades_df["session_date"] = (
        pd.to_datetime(
            trades_df["session_date"]
        ).dt.strftime("%Y-%m-%d")
    )

    trades_df["profile_date"] = (
        pd.to_datetime(
            trades_df["profile_date"]
        ).dt.strftime("%Y-%m-%d")
    )

    trades_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    winners = (
        trades_df["pnl_R"] > 0
    ).sum()

    losers = (
        trades_df["pnl_R"] < 0
    ).sum()

    total = len(
        trades_df
    )

    win_rate = (
        winners / total * 100
    )

    gross_profit = trades_df.loc[
        trades_df["pnl_R"] > 0,
        "pnl_R"
    ].sum()

    gross_loss = abs(
        trades_df.loc[
            trades_df["pnl_R"] < 0,
            "pnl_R"
        ].sum()
    )

    profit_factor = (
        gross_profit / gross_loss
        if gross_loss > 0
        else np.inf
    )

    expectancy = (
        trades_df["pnl_R"].mean()
    )

    total_r = (
        trades_df["pnl_R"].sum()
    )

    equity = (
        trades_df["pnl_R"]
        .cumsum()
    )

    running_max = (
        equity.cummax()
    )

    drawdown = (
        equity - running_max
    )

    max_dd = (
        drawdown.min()
    )

    # --------------------------------------------------------
    # LOSS STREAK
    # --------------------------------------------------------

    max_loss_streak = 0
    current_streak = 0

    for pnl in trades_df["pnl_R"]:

        if pnl < 0:

            current_streak += 1

            max_loss_streak = max(
                max_loss_streak,
                current_streak
            )

        else:

            current_streak = 0


    # ========================================================
    # PRINT RESULTS
    # ========================================================

    print()
    print("=" * 80)
    print("V2.2 BACKTEST RESULT")
    print("=" * 80)

    print(
        f"Total Trades     : {total:,}"
    )

    print(
        f"Winners          : {winners:,}"
    )

    print(
        f"Losers           : {losers:,}"
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
        f"Max Drawdown     : {max_dd:.2f}R"
    )

    print(
        f"Max Loss Streak  : {max_loss_streak}"
    )

    print()
    print("Session breakdown:")

    print(
        trades_df
        .groupby("session")["pnl_R"]
        .agg(["count", "sum"])
    )

    print()
    print("Direction breakdown:")

    print(
        trades_df
        .groupby("direction")["pnl_R"]
        .agg(["count", "sum"])
    )

    print()
    print("Level breakdown:")

    print(
        trades_df
        .groupby("level")["pnl_R"]
        .agg(["count", "sum"])
    )

    print()
    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print("=" * 80)
    print("V2.2 BACKTEST COMPLETE")
    print("=" * 80)