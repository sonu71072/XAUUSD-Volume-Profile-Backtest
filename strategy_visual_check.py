import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from volume_profile import calculate_volume_profile


# ============================================================
# SETTINGS
# ============================================================

DATA_FILE = Path("data/XAUUSD_M5.csv")

TIMEZONE = "Asia/Kolkata"

# Date to inspect
CHECK_DATE = "2026-09-11"

# Choose:
# "MORNING"
# "US_OPEN"
SESSION = "MORNING"

# Session times — IST
MORNING_START = "03:30"
MORNING_END = "06:00"

US_START = "18:55"
US_END = "19:55"

# Volume Profile
NUM_BINS = 100
VALUE_AREA_PERCENT = 0.70

# Candles to display BEFORE and AFTER session
BEFORE_CANDLES = 36
AFTER_CANDLES = 60


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("XAUUSD STRATEGY VISUAL CHECK")
print("=" * 70)

if not DATA_FILE.exists():
    print(f"❌ File not found: {DATA_FILE}")
    raise SystemExit

df = pd.read_csv(DATA_FILE)

df["time"] = pd.to_datetime(
    df["time"],
    utc=True
)

df["time_ist"] = df["time"].dt.tz_convert(
    TIMEZONE
)

df["date"] = df["time_ist"].dt.date


# ============================================================
# CHECK DATE
# ============================================================

check_date = pd.Timestamp(
    CHECK_DATE
).date()

day_data = df[
    df["date"] == check_date
].copy()

if day_data.empty:
    print(
        f"❌ No data found for {CHECK_DATE}"
    )
    raise SystemExit


# ============================================================
# SESSION FILTER
# ============================================================

if SESSION == "MORNING":

    start_time = MORNING_START
    end_time = MORNING_END

elif SESSION == "US_OPEN":

    start_time = US_START
    end_time = US_END

else:

    raise ValueError(
        "SESSION must be MORNING or US_OPEN"
    )


session_data = day_data[
    (
        day_data["time_ist"].dt.strftime("%H:%M")
        >= start_time
    )
    &
    (
        day_data["time_ist"].dt.strftime("%H:%M")
        <= end_time
    )
].copy()


# ============================================================
# VALIDATION
# ============================================================

if len(session_data) < 10:

    print(
        f"❌ Session has only "
        f"{len(session_data)} candles."
    )

    raise SystemExit


print("\nDate:", CHECK_DATE)
print("Session:", SESSION)

print(
    "Session start:",
    session_data["time_ist"].iloc[0]
)

print(
    "Session end:",
    session_data["time_ist"].iloc[-1]
)

print(
    "Session candles:",
    len(session_data)
)


# ============================================================
# SESSION RANGE
# ============================================================

session_high = session_data["high"].max()
session_low = session_data["low"].min()


# ============================================================
# VOLUME PROFILE
# ============================================================

profile = calculate_volume_profile(
    session_data,
    price_low=float(session_low),
    price_high=float(session_high),
    num_bins=NUM_BINS,
    value_area_percent=VALUE_AREA_PERCENT
)

if profile is None:

    print("❌ Volume Profile failed.")
    raise SystemExit


POC = profile["POC"]
VAH = profile["VAH"]
VAL = profile["VAL"]


# ============================================================
# GET SESSION INDEX
# ============================================================

session_start_index = session_data.index[0]
session_end_index = session_data.index[-1]


# ============================================================
# DISPLAY WINDOW
# ============================================================

start_index = max(
    0,
    session_start_index - BEFORE_CANDLES
)

end_index = min(
    len(df) - 1,
    session_end_index + AFTER_CANDLES
)

# Since dataframe index is sequential after CSV load
display_data = df.loc[
    start_index:end_index
].copy()


# ============================================================
# PLOT
# ============================================================

fig, ax = plt.subplots(
    figsize=(18, 9)
)


# ------------------------------------------------------------
# Candlesticks
# ------------------------------------------------------------

for i, (_, row) in enumerate(
    display_data.iterrows()
):

    candle_open = row["open"]
    candle_high = row["high"]
    candle_low = row["low"]
    candle_close = row["close"]

    # Wick
    ax.plot(
        [i, i],
        [candle_low, candle_high],
        linewidth=1
    )

    # Body
    body_low = min(
        candle_open,
        candle_close
    )

    body_high = max(
        candle_open,
        candle_close
    )

    body_height = (
        body_high - body_low
    )

    # Prevent zero-height candle
    if body_height == 0:
        body_height = 0.01

    if candle_close >= candle_open:
        face_color = "white"
    else:
        face_color = "black"

    ax.add_patch(
        plt.Rectangle(
            (
                i - 0.3,
                body_low
            ),
            0.6,
            body_height,
            facecolor=face_color,
            edgecolor="black"
        )
    )


# ============================================================
# PROFILE LEVELS
# ============================================================

ax.axhline(
    POC,
    linestyle="--",
    linewidth=2,
    label=f"POC {POC:.2f}"
)

ax.axhline(
    VAH,
    linestyle="--",
    linewidth=1.5,
    label=f"VAH {VAH:.2f}"
)

ax.axhline(
    VAL,
    linestyle="--",
    linewidth=1.5,
    label=f"VAL {VAL:.2f}"
)


# ============================================================
# SESSION HIGH / LOW
# ============================================================

ax.axhline(
    session_high,
    linestyle=":",
    linewidth=1,
    label=f"Session High {session_high:.2f}"
)

ax.axhline(
    session_low,
    linestyle=":",
    linewidth=1,
    label=f"Session Low {session_low:.2f}"
)


# ============================================================
# SESSION AREA
# ============================================================

session_positions = []

for i, (_, row) in enumerate(
    display_data.iterrows()
):

    current_time = row["time_ist"].strftime(
        "%H:%M"
    )

    if (
        start_time
        <= current_time
        <= end_time
    ):
        session_positions.append(i)


if session_positions:

    ax.axvspan(
        min(session_positions),
        max(session_positions),
        alpha=0.10,
        label=f"{SESSION} Session"
    )


# ============================================================
# X AXIS LABELS
# ============================================================

tick_positions = list(
    range(
        0,
        len(display_data),
        6
    )
)

tick_labels = [
    display_data["time_ist"]
    .iloc[i]
    .strftime("%m-%d %H:%M")
    for i in tick_positions
]

ax.set_xticks(
    tick_positions
)

ax.set_xticklabels(
    tick_labels,
    rotation=45,
    ha="right"
)


# ============================================================
# TITLE
# ============================================================

ax.set_title(
    f"XAUUSD M5 — {CHECK_DATE} — {SESSION}\n"
    f"VAH={VAH:.2f} | POC={POC:.2f} | VAL={VAL:.2f}"
)

ax.set_ylabel(
    "XAUUSD Price"
)

ax.set_xlabel(
    "Time (IST)"
)


# ============================================================
# GRID / LEGEND
# ============================================================

ax.grid(
    alpha=0.25
)

ax.legend(
    loc="best"
)

plt.tight_layout()


# ============================================================
# SAVE
# ============================================================

OUTPUT_DIR = Path("results")
OUTPUT_DIR.mkdir(
    exist_ok=True
)

output_file = (
    OUTPUT_DIR
    / f"{CHECK_DATE}_{SESSION}_visual.png"
)

plt.savefig(
    output_file,
    dpi=150,
    bbox_inches="tight"
)

print(
    "\n✅ Chart saved:"
)

print(
    output_file.resolve()
)


# ============================================================
# SHOW
# ============================================================

plt.show()