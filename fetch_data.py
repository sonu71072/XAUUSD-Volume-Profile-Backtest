import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta, timezone
from pathlib import Path


# =========================
# SETTINGS
# =========================

SYMBOL = "XAUUSD"
TIMEFRAME = mt5.TIMEFRAME_M5

# 2 years of data
YEARS = 2

OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "XAUUSD_M5.csv"


# =========================
# CREATE OUTPUT FOLDER
# =========================

OUTPUT_DIR.mkdir(exist_ok=True)


# =========================
# CONNECT TO MT5
# =========================

print("=" * 60)
print("XAUUSD M5 DATA FETCHER")
print("=" * 60)

print("\nConnecting to MetaTrader 5...")

if not mt5.initialize():
    print("❌ MT5 initialization failed")
    print("Error:", mt5.last_error())
    raise SystemExit

print("✅ MT5 connected")

print("MT5 version:", mt5.version())


# =========================
# CHECK SYMBOL
# =========================

symbol_info = mt5.symbol_info(SYMBOL)

if symbol_info is None:
    print(f"\n❌ Symbol '{SYMBOL}' not found.")

    print("\nAvailable symbols containing GOLD/XAU:")

    symbols = mt5.symbols_get()

    if symbols:
        for s in symbols:
            if "XAU" in s.name.upper() or "GOLD" in s.name.upper():
                print("  ", s.name)

    mt5.shutdown()
    raise SystemExit


print(f"\n✅ Symbol found: {SYMBOL}")


# Make sure symbol is visible
if not symbol_info.visible:

    print("Symbol not visible. Selecting it...")

    if not mt5.symbol_select(SYMBOL, True):
        print("❌ Could not select symbol")
        print("Error:", mt5.last_error())

        mt5.shutdown()
        raise SystemExit

    print("✅ Symbol selected")


# =========================
# DATE RANGE
# =========================

date_to = datetime.now(timezone.utc)
date_from = date_to - timedelta(days=365 * YEARS)

print("\nData range:")
print("From:", date_from)
print("To  :", date_to)


# =========================
# FETCH DATA
# =========================

print("\nFetching XAUUSD M5 data...")
print("Please wait...\n")

rates = mt5.copy_rates_range(
    SYMBOL,
    TIMEFRAME,
    date_from,
    date_to
)


# =========================
# CHECK RESULT
# =========================

if rates is None:

    print("❌ Data fetch failed")
    print("MT5 Error:", mt5.last_error())

    mt5.shutdown()
    raise SystemExit


if len(rates) == 0:

    print("❌ No data returned.")

    print("\nPossible reasons:")
    print("1. MT5 terminal does not have enough history")
    print("2. Symbol name is different")
    print("3. Market history is unavailable")
    print("4. Max bars in chart is too low")

    mt5.shutdown()
    raise SystemExit


print(f"✅ Data received: {len(rates):,} candles")


# =========================
# DATAFRAME
# =========================

df = pd.DataFrame(rates)


# Convert Unix timestamp → UTC datetime
df["time"] = pd.to_datetime(
    df["time"],
    unit="s",
    utc=True
)


# =========================
# CLEAN DATA
# =========================

# Remove duplicate candles
before = len(df)

df = df.drop_duplicates(
    subset=["time"]
).copy()

duplicates_removed = before - len(df)


# Sort oldest → newest
df = df.sort_values("time").reset_index(drop=True)


# =========================
# SELECT COLUMNS
# =========================

columns = [
    "time",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread",
    "real_volume"
]

df = df[columns]


# =========================
# CHECK DATA QUALITY
# =========================

print("\n" + "=" * 60)
print("DATA QUALITY")
print("=" * 60)

print("Candles:", f"{len(df):,}")
print("Duplicates removed:", duplicates_removed)

print("\nFirst candle:")
print(df.iloc[0])

print("\nLast candle:")
print(df.iloc[-1])


# =========================
# CHECK MISSING M5 CANDLES
# =========================

time_diff = df["time"].diff()

missing_gaps = df[
    time_diff > pd.Timedelta(minutes=5)
]

print("\nMissing/gap periods:", len(missing_gaps))

if len(missing_gaps) > 0:

    print("\nLargest gaps:")

    gaps = time_diff[time_diff > pd.Timedelta(minutes=5)]

    print(
        gaps.sort_values(
            ascending=False
        ).head(10)
    )


# =========================
# SAVE CSV
# =========================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================
# FINAL REPORT
# =========================

print("\n" + "=" * 60)
print("DOWNLOAD COMPLETE")
print("=" * 60)

print(f"\n✅ CSV saved to:")
print(OUTPUT_FILE.resolve())

print("\nFile size:")
print(
    f"{OUTPUT_FILE.stat().st_size / (1024 * 1024):.2f} MB"
)

print("\nFinal columns:")
print(list(df.columns))

print("\nSample data:")
print(df.head())

print("\nLast 5 candles:")
print(df.tail())


# =========================
# SHUTDOWN
# =========================

mt5.shutdown()

print("\n✅ MT5 connection closed")
print("✅ DONE")