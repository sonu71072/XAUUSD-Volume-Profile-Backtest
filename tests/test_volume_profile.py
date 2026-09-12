import pandas as pd

from volume_profile import calculate_volume_profile


# ---------------------------------------
# Load XAUUSD M5 data
# ---------------------------------------

FILE = "data/XAUUSD_M5.csv"

df = pd.read_csv(FILE)

df["time"] = pd.to_datetime(
    df["time"],
    utc=True
)


# ---------------------------------------
# Select a sample range
# ---------------------------------------

sample = df.iloc[-500:].copy()


print("=" * 60)
print("VOLUME PROFILE TEST")
print("=" * 60)

print("\nSample candles:", len(sample))

print(
    "From:",
    sample["time"].iloc[0]
)

print(
    "To  :",
    sample["time"].iloc[-1]
)


# ---------------------------------------
# Calculate Volume Profile
# ---------------------------------------

result = calculate_volume_profile(
    sample,
    num_bins=100,
    value_area_percent=0.70
)


# ---------------------------------------
# Print results
# ---------------------------------------

if result is None:

    print("\n❌ Volume Profile calculation failed.")

else:

    print("\n" + "=" * 60)
    print("VOLUME PROFILE")
    print("=" * 60)

    print(
        f"\nPOC : {result['POC']:.2f}"
    )

    print(
        f"VAH : {result['VAH']:.2f}"
    )

    print(
        f"VAL : {result['VAL']:.2f}"
    )

    print(
        f"\nTotal Volume: "
        f"{result['total_volume']:,.0f}"
    )

    print("\nProfile:")
    print(
        result["profile"].head(10)
    )

    print("\n✅ Volume Profile test successful.")