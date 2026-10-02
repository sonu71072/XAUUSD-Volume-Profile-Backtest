import pandas as pd
import numpy as np


# ============================================================
# V4 OUT-OF-SAMPLE BACKTEST
# V2 LOGIC + OOS DATE SPLIT
# ============================================================

DATA_FILE = "data/XAUUSD_M5.csv"
PROFILE_FILE = "data/session_profiles_v2.csv"
OUTPUT_FILE = "data/trades_v4_oos.csv"

# ============================================================
# V2 PARAMETERS — UNCHANGED
# ============================================================

RR = 2.0
LEVEL_TOLERANCE = 0.50
SWING_LOOKBACK = 3
MIN_SL_DISTANCE = 0.30
MAX_SL_DISTANCE = 15.0
ONE_TRADE_PER_SESSION = True
MAX_EXIT_CANDLES = 300

TIMEZONE = "Asia/Kolkata"

# ============================================================
# V4 SPLIT
# ============================================================

OOS_START_DATE = pd.Timestamp("2025-09-12").date()
OOS_END_DATE = pd.Timestamp("2026-09-11").date()


# ============================================================
# SESSION FUNCTION
# ============================================================

def get_session(timestamp):

    local_time = timestamp.tz_convert(TIMEZONE)

    if local_time.weekday() >= 5:
        return None, None

    t = local_time.time()

    morning_start = pd.Timestamp("03:30:00").time()
    morning_end = pd.Timestamp("06:00:00").time()

    us_start = pd.Timestamp("18:55:00").time()
    us_end = pd.Timestamp("19:55:00").time()

    if morning_start <= t < morning_end:
        return "MORNING", local_time.date()

    if us_start <= t < us_end:
        return "US_OPEN", local_time.date()

    return None, None


# ============================================================
# PROFILE DATE CLEANER
# ============================================================

def clean_profile_date(value):

    if pd.isna(value):
        return None

    value = str(value).strip()

    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


# ============================================================
# START
# ============================================================

print()
print("=" * 80)
print("V4 OUT-OF-SAMPLE BACKTEST")
print("=" * 80)


# ============================================================
# LOAD MARKET DATA
# ============================================================

print()
print("Loading market data...")

df = pd.read_csv(DATA_FILE)

df["time"] = pd.to_datetime(
    df["time"],
    utc=True
)

df = df.sort_values(
    "time"
).reset_index(drop=True)

print(
    f"Market candles loaded : {len(df):,}"
)

print(
    f"Market start          : {df['time'].min()}"
)

print(
    f"Market end            : {df['time'].max()}"
)


# ============================================================
# ASSIGN SESSION
# ============================================================

print()
print("Assigning sessions...")

df["session"] = None
df["session_date"] = None

for i in range(len(df)):

    session, session_date = get_session(
        df.loc[i, "time"]
    )

    df.loc[i, "session"] = session
    df.loc[i, "session_date"] = session_date


# ============================================================
# LOAD V2 CAUSAL PROFILES
# ============================================================

print()
print("Loading V2 causal profiles...")

profiles = pd.read_csv(
    PROFILE_FILE
)

profiles["session_date"] = (
    pd.to_datetime(
        profiles["session_date"]
    ).dt.date
)

profiles["profile_date"] = (
    profiles["profile_date"]
    .apply(clean_profile_date)
)

profiles = profiles.dropna(
    subset=[
        "session_date",
        "profile_date"
    ]
)

profiles = profiles.sort_values(
    [
        "session_date",
        "session"
    ]
).reset_index(drop=True)

print(
    f"Profiles loaded       : {len(profiles):,}"
)


# ============================================================
# BUILD PROFILE LOOKUP
# ============================================================

profile_lookup = {}

for _, p in profiles.iterrows():

    key = (
        p["session_date"],
        p["session"]
    )

    profile_lookup[key] = {

        "poc":
            float(p["POC"]),

        "vah":
            float(p["VAH"]),

        "val":
            float(p["VAL"]),

        "profile_date":
            p["profile_date"],
    }


# ============================================================
# PROFILE DIAGNOSTIC
# ============================================================

oos_profiles = profiles[
    (
        profiles["session_date"]
        >= OOS_START_DATE
    )
    &
    (
        profiles["session_date"]
        <= OOS_END_DATE
    )
]

print()
print(
    f"OOS profiles          : {len(oos_profiles):,}"
)

print(
    f"OOS MORNING profiles  : "
    f"{len(oos_profiles[oos_profiles['session'] == 'MORNING']):,}"
)

print(
    f"OOS US_OPEN profiles  : "
    f"{len(oos_profiles[oos_profiles['session'] == 'US_OPEN']):,}"
)


# ============================================================
# MAIN BACKTEST
# ============================================================

trades = []

used_sessions = set()

print()
print("Running OOS strategy...")


for i in range(
    SWING_LOOKBACK + 2,
    len(df) - 1
):

    row = df.iloc[i]

    signal_time = row["time"]

    session = row["session"]
    session_date = row["session_date"]

    # --------------------------------------------------------
    # ONLY TRADE OOS SESSION DATES
    # --------------------------------------------------------

    if session_date is None:
        continue

    if session_date < OOS_START_DATE:
        continue

    if session_date > OOS_END_DATE:
        continue

    # --------------------------------------------------------
    # SESSION KEY
    # --------------------------------------------------------

    session_key = (
        session_date,
        session
    )

    if (
        ONE_TRADE_PER_SESSION
        and session_key in used_sessions
    ):
        continue

    # --------------------------------------------------------
    # PROFILE
    # --------------------------------------------------------

    profile_key = (
        session_date,
        session
    )

    if profile_key not in profile_lookup:
        continue

    profile = profile_lookup[
        profile_key
    ]

    profile_date = profile[
        "profile_date"
    ]

    # --------------------------------------------------------
    # HARD CAUSALITY
    # --------------------------------------------------------

    if profile_date >= session_date:
        continue

    poc = profile["poc"]
    vah = profile["vah"]
    val = profile["val"]

    # --------------------------------------------------------
    # CURRENT CANDLE
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
    # LEVEL DETECTION
    # ========================================================

    buy_level = None
    sell_level = None

    levels = [
        ("POC", poc),
        ("VAH", vah),
        ("VAL", val),
    ]

    # ========================================================
    # BUY SIGNAL
    # ========================================================

    for level_name, level in levels:

        if (
            current_low <= level + LEVEL_TOLERANCE
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

    for level_name, level in levels:

        if (
            current_high >= level - LEVEL_TOLERANCE
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
            ]["low"].min()
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

                # SL FIRST
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
            ]["high"].max()
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

                # SL FIRST
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
    print("=" * 80)
    print("NO OOS TRADES GENERATED")
    print("=" * 80)

else:

    # --------------------------------------------------------
    # CLEAN DATES
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

    # --------------------------------------------------------
    # BASIC STATS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # DRAW DOWN
    # --------------------------------------------------------

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
    # FINAL REPORT
    # ========================================================

    print()
    print("=" * 80)
    print("V4 OUT-OF-SAMPLE BACKTEST RESULT")
    print("=" * 80)

    print()
    print("OOS PERIOD")
    print("-" * 80)

    print(
        f"{OOS_START_DATE} -> {OOS_END_DATE}"
    )

    print()
    print("PERFORMANCE")
    print("-" * 80)

    print(
        f"Total Trades       : {total:,}"
    )

    print(
        f"Winners            : {winners:,}"
    )

    print(
        f"Losers             : {losers:,}"
    )

    print(
        f"Win Rate           : {win_rate:.2f}%"
    )

    print(
        f"Profit Factor      : {profit_factor:.2f}"
    )

    print(
        f"Total R            : {total_r:.2f}R"
    )

    print(
        f"Expectancy         : {expectancy:.3f}R"
    )

    print(
        f"Max Drawdown       : {max_dd:.2f}R"
    )

    print(
        f"Max Loss Streak    : {max_loss_streak}"
    )

    print()
    print("SESSION BREAKDOWN")
    print("-" * 80)

    print(
        trades_df
        .groupby("session")["pnl_R"]
        .agg(
            ["count", "sum", "mean"]
        )
    )

    print()
    print("DIRECTION BREAKDOWN")
    print("-" * 80)

    print(
        trades_df
        .groupby("direction")["pnl_R"]
        .agg(
            ["count", "sum", "mean"]
        )
    )

    print()
    print("LEVEL BREAKDOWN")
    print("-" * 80)

    print(
        trades_df
        .groupby("level")["pnl_R"]
        .agg(
            ["count", "sum", "mean"]
        )
    )

    print()
    print("EXIT BREAKDOWN")
    print("-" * 80)

    print(
        trades_df
        .groupby("exit_reason")["pnl_R"]
        .agg(
            ["count", "sum", "mean"]
        )
    )

    print()
    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print("=" * 80)
    print("V4 OOS BACKTEST COMPLETE")
    print("=" * 80)