import pandas as pd

from src.volume_profile import calculate_volume_profile


# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = "data/XAUUSD_M5.csv"
OUTPUT_FILE = "data/session_profiles_v2.csv"

TIMEZONE = "Asia/Kolkata"

VALUE_AREA_PERCENT = 0.70


# ============================================================
# SESSION FUNCTION
# ============================================================

def get_session(timestamp):
    """
    Assign trading session using Asia/Kolkata time.

    MORNING:
        03:30 - 06:00 IST

    US_OPEN:
        18:55 - 19:55 IST
    """

    ts = timestamp.tz_convert(TIMEZONE)

    # Weekends excluded
    if ts.weekday() >= 5:
        return None

    minutes = ts.hour * 60 + ts.minute

    # --------------------------------------------------------
    # MORNING
    # --------------------------------------------------------

    if (
        3 * 60 + 30
        <= minutes
        < 6 * 60
    ):
        return "MORNING"

    # --------------------------------------------------------
    # US OPEN
    # --------------------------------------------------------

    if (
        18 * 60 + 55
        <= minutes
        < 19 * 60 + 55
    ):
        return "US_OPEN"

    return None


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 80)
print("V2.1 — CAUSAL SESSION PROFILE")
print("=" * 80)

df = pd.read_csv(
    INPUT_FILE,
    parse_dates=["time"]
)

df = df.sort_values("time").reset_index(drop=True)

# Ensure UTC timezone
if df["time"].dt.tz is None:
    df["time"] = df["time"].dt.tz_localize("UTC")

print(f"Loaded candles : {len(df):,}")


# ============================================================
# SESSION ASSIGNMENT
# ============================================================

df["session"] = df["time"].apply(get_session)

df["session_date"] = (
    df["time"]
    .dt.tz_convert(TIMEZONE)
    .dt.date
)

# Keep only valid sessions
session_df = df[
    df["session"].notna()
].copy()


# ============================================================
# GROUP SESSIONS
# ============================================================

session_groups = (
    session_df
    .groupby(
        ["session_date", "session"],
        sort=True
    )
)

session_keys = list(
    session_groups.groups.keys()
)


# ============================================================
# BUILD CAUSAL PROFILES
# ============================================================

profiles = []

for current_key in session_keys:

    current_session_date, current_session = current_key

    # --------------------------------------------------------
    # Find previous completed SAME-TYPE session
    # --------------------------------------------------------

    previous_keys = [
        key
        for key in session_keys
        if (
            key[1] == current_session
            and key[0] < current_session_date
        )
    ]

    if not previous_keys:
        continue

    previous_key = previous_keys[-1]

    previous_session_date, previous_session = previous_key

    previous_data = session_groups.get_group(
        previous_key
    ).copy()

    # --------------------------------------------------------
    # Require enough candles
    # --------------------------------------------------------

    if len(previous_data) < 7:
        continue

    # --------------------------------------------------------
    # Calculate profile ONLY from previous session
    # --------------------------------------------------------

    profile = calculate_volume_profile(
        previous_data,
        value_area_percent=VALUE_AREA_PERCENT
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # profile_date = ONLY the previous date
    #
    # DO NOT save (date, session)
    # --------------------------------------------------------

    profiles.append({

        "session_date": current_session_date,

        "session": current_session,

        "profile_date": previous_session_date,

        "profile_high": float(
            previous_data["high"].max()
        ),

        "profile_low": float(
            previous_data["low"].min()
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

        "profile_volume": float(
            previous_data["tick_volume"].sum()
        ),

        "profile_candles": int(
            len(previous_data)
        ),
    })


# ============================================================
# CREATE OUTPUT DATAFRAME
# ============================================================

profiles_df = pd.DataFrame(profiles)


# ============================================================
# CLEAN DATE COLUMNS
# ============================================================

if not profiles_df.empty:

    profiles_df["session_date"] = pd.to_datetime(
        profiles_df["session_date"]
    ).dt.strftime("%Y-%m-%d")

    profiles_df["profile_date"] = pd.to_datetime(
        profiles_df["profile_date"]
    ).dt.strftime("%Y-%m-%d")


# ============================================================
# SAVE
# ============================================================

profiles_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# RESULTS
# ============================================================

print()
print(
    f"Generated profiles : "
    f"{len(profiles_df):,}"
)

if not profiles_df.empty:

    print()
    print("Session breakdown:")

    print(
        profiles_df["session"]
        .value_counts()
        .sort_index()
    )

    print()
    print("Latest V2 profiles:")

    print(
        profiles_df.tail(5)
        .to_string(index=False)
    )

print()
print(
    f"Saved to: {OUTPUT_FILE}"
)

print("=" * 80)
print("V2.1 PROFILE GENERATION COMPLETE")
print("=" * 80)