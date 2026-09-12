import pandas as pd
from pathlib import Path

from volume_profile import calculate_volume_profile


# ============================================================
# SETTINGS
# ============================================================

INPUT_FILE = Path("data/XAUUSD_M5.csv")
OUTPUT_FILE = Path("data/session_profiles.csv")

TIMEZONE = "Asia/Kolkata"

# Session timings in IST
MORNING_START = "03:30"
MORNING_END = "06:00"

US_START = "18:55"
US_END = "19:55"

# Volume Profile settings
NUM_BINS = 100
VALUE_AREA_PERCENT = 0.70

# Minimum candles required
MIN_MORNING_CANDLES = 10
MIN_US_CANDLES = 10


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("XAUUSD SESSION VOLUME PROFILE ENGINE")
print("=" * 70)

print("\nLoading XAUUSD M5 data...")

if not INPUT_FILE.exists():
    print(f"❌ File not found: {INPUT_FILE}")
    raise SystemExit

df = pd.read_csv(INPUT_FILE)

print(f"✅ Loaded {len(df):,} candles")


# ============================================================
# DATETIME
# ============================================================

df["time"] = pd.to_datetime(
    df["time"],
    utc=True
)

df["time_ist"] = df["time"].dt.tz_convert(
    TIMEZONE
)

df["date"] = df["time_ist"].dt.date
df["weekday"] = df["time_ist"].dt.weekday
df["time_only"] = df["time_ist"].dt.strftime("%H:%M")


# ============================================================
# WEEKDAY FILTER
# ============================================================

# Monday = 0
# Tuesday = 1
# Wednesday = 2
# Thursday = 3
# Friday = 4
# Saturday = 5
# Sunday = 6

df = df[
    df["weekday"] <= 4
].copy()

print(
    f"After weekday filter: {len(df):,} candles"
)


# ============================================================
# SESSION IDENTIFICATION
# ============================================================

def identify_session(time_string):

    if (
        MORNING_START
        <= time_string
        <= MORNING_END
    ):
        return "MORNING"

    if (
        US_START
        <= time_string
        <= US_END
    ):
        return "US_OPEN"

    return None


df["session"] = df["time_only"].apply(
    identify_session
)


session_df = df[
    df["session"].notna()
].copy()


print(
    f"Session candles: {len(session_df):,}"
)


# ============================================================
# PROCESS EACH SESSION
# ============================================================

results = []

grouped = session_df.groupby(
    ["date", "session"]
)


print("\nCalculating session profiles...")


for (date, session), group in grouped:

    group = group.sort_values(
        "time_ist"
    ).copy()

    candle_count = len(group)

    # --------------------------------------------------------
    # Minimum candle validation
    # --------------------------------------------------------

    if session == "MORNING":

        if candle_count < MIN_MORNING_CANDLES:
            print(
                f"⚠️ Skipping {date} MORNING "
                f"({candle_count} candles)"
            )
            continue

    elif session == "US_OPEN":

        if candle_count < MIN_US_CANDLES:
            print(
                f"⚠️ Skipping {date} US_OPEN "
                f"({candle_count} candles)"
            )
            continue

    # --------------------------------------------------------
    # Session range
    # --------------------------------------------------------

    session_high = group["high"].max()
    session_low = group["low"].min()

    session_range = (
        session_high
        - session_low
    )

    # --------------------------------------------------------
    # Volume Profile
    # --------------------------------------------------------

    profile = calculate_volume_profile(
        group,
        price_low=float(session_low),
        price_high=float(session_high),
        num_bins=NUM_BINS,
        value_area_percent=VALUE_AREA_PERCENT
    )

    if profile is None:

        print(
            f"❌ Profile failed: "
            f"{date} {session}"
        )

        continue

    # --------------------------------------------------------
    # Save result
    # --------------------------------------------------------

    results.append({

        "date": date,

        "session": session,

        "session_start": group[
            "time_ist"
        ].iloc[0],

        "session_end": group[
            "time_ist"
        ].iloc[-1],

        "candles": candle_count,

        "session_high": float(
            session_high
        ),

        "session_low": float(
            session_low
        ),

        "session_range": float(
            session_range
        ),

        "POC": float(
            profile["POC"]
        ),

        "VAH": float(
            profile["VAH"]
        ),

        "VAL": float(
            profile["VAL"]
        ),

        "total_volume": float(
            profile["total_volume"]
        )
    })


# ============================================================
# CREATE RESULT DATAFRAME
# ============================================================

result_df = pd.DataFrame(
    results
)


# ============================================================
# SORT
# ============================================================

if not result_df.empty:

    result_df = result_df.sort_values(
        ["date", "session"]
    ).reset_index(
        drop=True
    )


# ============================================================
# SAVE
# ============================================================

result_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# REPORT
# ============================================================

print("\n" + "=" * 70)
print("SESSION PROFILE RESULTS")
print("=" * 70)

print(
    f"\nValid session profiles: "
    f"{len(result_df):,}"
)

if not result_df.empty:

    print(
        "\nMorning profiles:",
        len(
            result_df[
                result_df["session"]
                == "MORNING"
            ]
        )
    )

    print(
        "US Open profiles:",
        len(
            result_df[
                result_df["session"]
                == "US_OPEN"
            ]
        )
    )

    print(
        "\nFirst 10 profiles:"
    )

    print(
        result_df.head(10).to_string(
            index=False
        )
    )

    print(
        "\nLast 10 profiles:"
    )

    print(
        result_df.tail(10).to_string(
            index=False
        )
    )


# ============================================================
# STATISTICS
# ============================================================

if not result_df.empty:

    print(
        "\n" + "=" * 70
    )

    print(
        "PROFILE STATISTICS"
    )

    print(
        "=" * 70
    )

    for session_name in [
        "MORNING",
        "US_OPEN"
    ]:

        temp = result_df[
            result_df["session"]
            == session_name
        ]

        if temp.empty:
            continue

        print(
            f"\n{session_name}"
        )

        print(
            f"Average range: "
            f"{temp['session_range'].mean():.2f}"
        )

        print(
            f"Median range: "
            f"{temp['session_range'].median():.2f}"
        )

        print(
            f"Average volume: "
            f"{temp['total_volume'].mean():,.0f}"
        )


# ============================================================
# FILE LOCATION
# ============================================================

print(
    "\n" + "=" * 70
)

print("FILE SAVED")

print("=" * 70)

print(
    OUTPUT_FILE.resolve()
)

print(
    "\n✅ SESSION PROFILE ENGINE COMPLETE"
)