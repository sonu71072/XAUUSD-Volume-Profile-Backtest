import pandas as pd
from pathlib import Path


# ============================================================
# SETTINGS
# ============================================================

INPUT_FILE = Path("data/XAUUSD_M5.csv")
OUTPUT_FILE = Path("data/XAUUSD_M5_sessions.csv")

# CSV time is UTC
UTC_COLUMN = "time"

# Convert UTC -> India Standard Time
LOCAL_TIMEZONE = "Asia/Kolkata"


# ============================================================
# SESSION TIMES — INDIA TIME
# ============================================================

MORNING_START = "03:30"
MORNING_END = "06:00"

US_START = "18:55"
US_END = "19:55"


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 65)
print("XAUUSD SESSION ENGINE")
print("=" * 65)

print("\nLoading data...")

if not INPUT_FILE.exists():
    print(f"❌ File not found: {INPUT_FILE}")
    raise SystemExit

df = pd.read_csv(INPUT_FILE)

print(f"✅ Loaded {len(df):,} candles")


# ============================================================
# DATETIME
# ============================================================

df[UTC_COLUMN] = pd.to_datetime(
    df[UTC_COLUMN],
    utc=True
)

# Convert to IST
df["time_ist"] = df[UTC_COLUMN].dt.tz_convert(
    LOCAL_TIMEZONE
)


# ============================================================
# TRADING DATE
# ============================================================

df["trading_date"] = (
    df["time_ist"]
    .dt
    .date
)


# ============================================================
# TIME OF DAY
# ============================================================

df["time_only"] = (
    df["time_ist"]
    .dt
    .strftime("%H:%M")
)


# ============================================================
# SESSION FUNCTION
# ============================================================

def get_session(time_string):

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

    return "NONE"


df["session"] = df["time_only"].apply(
    get_session
)


# ============================================================
# SESSION ID
# ============================================================

df["session_id"] = (
    df["trading_date"].astype(str)
    + "_"
    + df["session"]
)


# ============================================================
# SESSION RANGE
# ============================================================

df["session_high"] = pd.NA
df["session_low"] = pd.NA


# ------------------------------------------------------------
# Morning Session
# ------------------------------------------------------------

morning_mask = (
    df["session"] == "MORNING"
)

morning_high = (
    df.loc[morning_mask]
    .groupby("trading_date")["high"]
    .transform("max")
)

morning_low = (
    df.loc[morning_mask]
    .groupby("trading_date")["low"]
    .transform("min")
)

df.loc[morning_mask, "session_high"] = (
    morning_high
)

df.loc[morning_mask, "session_low"] = (
    morning_low
)


# ------------------------------------------------------------
# US Session
# ------------------------------------------------------------

us_mask = (
    df["session"] == "US_OPEN"
)

us_high = (
    df.loc[us_mask]
    .groupby("trading_date")["high"]
    .transform("max")
)

us_low = (
    df.loc[us_mask]
    .groupby("trading_date")["low"]
    .transform("min")
)

df.loc[us_mask, "session_high"] = (
    us_high
)

df.loc[us_mask, "session_low"] = (
    us_low
)


# ============================================================
# SESSION SUMMARY
# ============================================================

session_data = df[
    df["session"] != "NONE"
].copy()


summary = (
    session_data
    .groupby(
        ["trading_date", "session"],
        as_index=False
    )
    .agg(
        session_start=("time_ist", "min"),
        session_end=("time_ist", "max"),
        session_high=("high", "max"),
        session_low=("low", "min"),
        candles=("close", "count"),
        volume=("tick_volume", "sum")
    )
)


summary["range"] = (
    summary["session_high"]
    - summary["session_low"]
)


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# REPORT
# ============================================================

print("\n" + "=" * 65)
print("SESSION ANALYSIS")
print("=" * 65)

print(
    "\nMorning sessions:",
    len(
        summary[
            summary["session"] == "MORNING"
        ]
    )
)

print(
    "US sessions:",
    len(
        summary[
            summary["session"] == "US_OPEN"
        ]
    )
)

print(
    "\nTotal session records:",
    len(summary)
)


print("\n" + "=" * 65)
print("LAST 20 SESSION RECORDS")
print("=" * 65)

print(
    summary.tail(20).to_string(
        index=False
    )
)


# ============================================================
# SAVE SUMMARY
# ============================================================

SUMMARY_FILE = Path(
    "data/session_summary.csv"
)

summary.to_csv(
    SUMMARY_FILE,
    index=False
)


print("\n" + "=" * 65)
print("FILES SAVED")
print("=" * 65)

print(
    "\nMain file:"
)

print(
    OUTPUT_FILE.resolve()
)

print(
    "\nSession summary:"
)

print(
    SUMMARY_FILE.resolve()
)

print("\n✅ SESSION ENGINE COMPLETE")