import os
import numpy as np
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

DATA_FILE = "data/XAUUSD_M5.csv"
PROFILE_FILE = "data/session_profiles.csv"
OUTPUT_FILE = "data/trades_v1.csv"

TZ = "Asia/Kolkata"

RR = 2.0

LEVEL_TOLERANCE = 0.50

SWING_LOOKBACK = 3

MIN_SL_DISTANCE = 0.30
MAX_SL_DISTANCE = 15.0

ONE_TRADE_PER_SESSION = True

MAX_EXIT_CANDLES = 300


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("XAUUSD V1 OPTIMIZED STRATEGY ENGINE")
print("=" * 70)


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading market data...")

market = pd.read_csv(DATA_FILE)

profiles = pd.read_csv(PROFILE_FILE)

print(f"Market candles : {len(market):,}")
print(f"Profiles       : {len(profiles):,}")


# ============================================================
# TIME CONVERSION
# ============================================================

market["time"] = pd.to_datetime(
    market["time"],
    utc=True
).dt.tz_convert(TZ)

profiles["session_start"] = pd.to_datetime(
    profiles["session_start"],
    utc=True
).dt.tz_convert(TZ)

profiles["session_end"] = pd.to_datetime(
    profiles["session_end"],
    utc=True
).dt.tz_convert(TZ)


# ============================================================
# SORT
# ============================================================

market = market.sort_values("time").reset_index(drop=True)

profiles = profiles.sort_values(
    ["session_start", "session"]
).reset_index(drop=True)


# ============================================================
# MARKET ARRAYS
# ============================================================

market_times = market["time"]

opens = market["open"].to_numpy(dtype=float)

highs = market["high"].to_numpy(dtype=float)

lows = market["low"].to_numpy(dtype=float)

closes = market["close"].to_numpy(dtype=float)


# ============================================================
# BUILD DATE INDEX
# ============================================================

print("\nBuilding date index...")

market_dates = market_times.dt.date.to_numpy()

date_indices = {}

for i, d in enumerate(market_dates):

    if d not in date_indices:
        date_indices[d] = []

    date_indices[d].append(i)


# Convert lists to numpy arrays

for d in date_indices:
    date_indices[d] = np.asarray(
        date_indices[d],
        dtype=np.int64
    )


# ============================================================
# FIND FIRST CANDLE AFTER SESSION
# ============================================================

def find_first_after(day_indices, session_end):

    if day_indices is None or len(day_indices) == 0:
        return None

    # Pandas Series of timestamps
    day_times = market_times.iloc[day_indices]

    # Make sure timestamps are timezone aware
    if day_times.dt.tz is None:

        day_times = (
            day_times
            .dt
            .tz_localize("UTC")
            .dt
            .tz_convert(TZ)
        )

    else:

        day_times = day_times.dt.tz_convert(TZ)

    # Make session_end timezone aware
    if session_end.tzinfo is None:

        session_end = session_end.tz_localize(TZ)

    else:

        session_end = session_end.tz_convert(TZ)

    # First candle strictly AFTER session end
    mask = day_times > session_end

    positions = np.flatnonzero(
        mask.to_numpy()
    )

    if len(positions) == 0:
        return None

    return int(day_indices[positions[0]])


# ============================================================
# FIND EXIT
# ============================================================

def check_trade_exit(
    entry_index,
    direction,
    entry_price,
    stop_loss,
    take_profit,
    day_indices
):

    if day_indices is None:
        return None

    # Only candles after entry
    future_indices = day_indices[
        day_indices > entry_index
    ]

    if len(future_indices) == 0:
        return None

    # Limit scan
    future_indices = future_indices[
        :MAX_EXIT_CANDLES
    ]

    for idx in future_indices:

        high = highs[idx]
        low = lows[idx]

        # ----------------------------------------------------
        # BUY
        # ----------------------------------------------------

        if direction == "BUY":

            hit_sl = low <= stop_loss
            hit_tp = high >= take_profit

            # Conservative assumption:
            # if both happen in same candle,
            # assume SL happened first.
            if hit_sl and hit_tp:

                return {
                    "exit_index": int(idx),
                    "exit_price": float(stop_loss),
                    "result": "LOSS",
                    "r_multiple": -1.0
                }

            if hit_sl:

                return {
                    "exit_index": int(idx),
                    "exit_price": float(stop_loss),
                    "result": "LOSS",
                    "r_multiple": -1.0
                }

            if hit_tp:

                return {
                    "exit_index": int(idx),
                    "exit_price": float(take_profit),
                    "result": "WIN",
                    "r_multiple": RR
                }

        # ----------------------------------------------------
        # SELL
        # ----------------------------------------------------

        else:

            hit_sl = high >= stop_loss
            hit_tp = low <= take_profit

            # Conservative assumption
            if hit_sl and hit_tp:

                return {
                    "exit_index": int(idx),
                    "exit_price": float(stop_loss),
                    "result": "LOSS",
                    "r_multiple": -1.0
                }

            if hit_sl:

                return {
                    "exit_index": int(idx),
                    "exit_price": float(stop_loss),
                    "result": "LOSS",
                    "r_multiple": -1.0
                }

            if hit_tp:

                return {
                    "exit_index": int(idx),
                    "exit_price": float(take_profit),
                    "result": "WIN",
                    "r_multiple": RR
                }

    # No SL / TP hit
    return None


# ============================================================
# SIGNAL GENERATION
# ============================================================

print("\nGenerating signals...")

trades = []

total_profiles = len(profiles)

for profile_number, profile in profiles.iterrows():

    if profile_number == 0 or (profile_number + 1) % 50 == 0:

        print(
            f"Processing profiles: "
            f"{profile_number + 1}/{total_profiles}"
        )

    session_date = profile["session_start"].date()

    session_end = profile["session_end"]

    session_name = profile["session"]

    # --------------------------------------------------------
    # GET PROFILE LEVELS
    # --------------------------------------------------------

    try:

        vah = float(profile["VAH"])

        val = float(profile["VAL"])

        poc = float(profile["POC"])

    except Exception:

        continue

    levels = {
        "VAH": vah,
        "POC": poc,
        "VAL": val
    }

    # --------------------------------------------------------
    # GET THAT DAY'S MARKET CANDLES
    # --------------------------------------------------------

    day_indices = date_indices.get(
        session_date
    )

    if day_indices is None:
        continue

    # --------------------------------------------------------
    # FIRST CANDLE AFTER SESSION
    # --------------------------------------------------------

    start_idx = find_first_after(
        day_indices,
        session_end
    )

    if start_idx is None:
        continue

    # Position inside day_indices
    start_positions = np.flatnonzero(
        day_indices >= start_idx
    )

    if len(start_positions) == 0:
        continue

    start_pos = int(start_positions[0])

    scan_indices = day_indices[start_pos:]

    trade_taken = False

    # --------------------------------------------------------
    # SCAN CANDLES
    # --------------------------------------------------------

    for idx in scan_indices:

        idx = int(idx)

        # Need previous candle
        if idx < SWING_LOOKBACK:
            continue

        current_open = opens[idx]

        current_high = highs[idx]

        current_low = lows[idx]

        current_close = closes[idx]

        previous_close = closes[idx - 1]

        # ----------------------------------------------------
        # ONE TRADE PER SESSION
        # ----------------------------------------------------

        if (
            ONE_TRADE_PER_SESSION
            and trade_taken
        ):
            break

        # ----------------------------------------------------
        # CHECK EACH PROFILE LEVEL
        # ----------------------------------------------------

        signal_found = False

        for level_name, level in levels.items():

            # =================================================
            # BUY REJECTION
            # =================================================

            buy_signal = (

                current_low
                <= level + LEVEL_TOLERANCE

                and

                current_close
                > level

                and

                previous_close
                <= level

            )

            if buy_signal:

                # ---------------------------------------------
                # Previous swing low
                # ---------------------------------------------

                swing_start = max(
                    0,
                    idx - SWING_LOOKBACK
                )

                swing_low = np.min(
                    lows[
                        swing_start:idx
                    ]
                )

                stop_loss = float(
                    swing_low
                )

                entry_price = float(
                    current_open
                )

                risk = (
                    entry_price
                    - stop_loss
                )

                # Valid SL
                if (
                    risk >= MIN_SL_DISTANCE
                    and
                    risk <= MAX_SL_DISTANCE
                ):

                    take_profit = (
                        entry_price
                        + RR * risk
                    )

                    exit_data = check_trade_exit(
                        entry_index=idx,
                        direction="BUY",
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        day_indices=day_indices
                    )

                    trade = {
                        "date": str(session_date),
                        "session": session_name,
                        "direction": "BUY",
                        "level": level_name,
                        "level_price": level,
                        "entry_time": str(
                            market_times.iloc[idx]
                        ),
                        "entry_price": entry_price,
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "risk": risk
                    }

                    if exit_data is not None:

                        exit_idx = exit_data[
                            "exit_index"
                        ]

                        trade.update({

                            "exit_time": str(
                                market_times.iloc[
                                    exit_idx
                                ]
                            ),

                            "exit_price":
                                exit_data[
                                    "exit_price"
                                ],

                            "result":
                                exit_data[
                                    "result"
                                ],

                            "r_multiple":
                                exit_data[
                                    "r_multiple"
                                ]
                        })

                    else:

                        trade.update({

                            "exit_time": None,

                            "exit_price": None,

                            "result": "OPEN",

                            "r_multiple": None
                        })

                    trades.append(trade)

                    trade_taken = True

                    signal_found = True

                    break

            # =================================================
            # SELL REJECTION
            # =================================================

            sell_signal = (

                current_high
                >= level - LEVEL_TOLERANCE

                and

                current_close
                < level

                and

                previous_close
                >= level

            )

            if sell_signal:

                # ---------------------------------------------
                # Previous swing high
                # ---------------------------------------------

                swing_start = max(
                    0,
                    idx - SWING_LOOKBACK
                )

                swing_high = np.max(
                    highs[
                        swing_start:idx
                    ]
                )

                stop_loss = float(
                    swing_high
                )

                entry_price = float(
                    current_open
                )

                risk = (
                    stop_loss
                    - entry_price
                )

                # Valid SL
                if (
                    risk >= MIN_SL_DISTANCE
                    and
                    risk <= MAX_SL_DISTANCE
                ):

                    take_profit = (
                        entry_price
                        - RR * risk
                    )

                    exit_data = check_trade_exit(
                        entry_index=idx,
                        direction="SELL",
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        day_indices=day_indices
                    )

                    trade = {
                        "date": str(session_date),
                        "session": session_name,
                        "direction": "SELL",
                        "level": level_name,
                        "level_price": level,
                        "entry_time": str(
                            market_times.iloc[idx]
                        ),
                        "entry_price": entry_price,
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "risk": risk
                    }

                    if exit_data is not None:

                        exit_idx = exit_data[
                            "exit_index"
                        ]

                        trade.update({

                            "exit_time": str(
                                market_times.iloc[
                                    exit_idx
                                ]
                            ),

                            "exit_price":
                                exit_data[
                                    "exit_price"
                                ],

                            "result":
                                exit_data[
                                    "result"
                                ],

                            "r_multiple":
                                exit_data[
                                    "r_multiple"
                                ]
                        })

                    else:

                        trade.update({

                            "exit_time": None,

                            "exit_price": None,

                            "result": "OPEN",

                            "r_multiple": None
                        })

                    trades.append(trade)

                    trade_taken = True

                    signal_found = True

                    break

        # Stop scanning after trade
        if signal_found:

            break


# ============================================================
# CREATE TRADE DATAFRAME
# ============================================================

print("\nSignal generation completed.")

trades_df = pd.DataFrame(trades)

if len(trades_df) == 0:

    print("\nNo trades generated.")

    print(
        "\nPossible reasons:"
    )

    print(
        "1. Entry conditions are too strict."
    )

    print(
        "2. Profile levels are not being reached."
    )

    print(
        "3. Profile column names are different."
    )

    raise SystemExit


# ============================================================
# SAVE
# ============================================================

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

trades_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# RESULTS
# ============================================================

closed = trades_df[
    trades_df["result"].isin(
        ["WIN", "LOSS"]
    )
].copy()

open_trades = trades_df[
    trades_df["result"] == "OPEN"
]


total_signals = len(trades_df)

closed_count = len(closed)

open_count = len(open_trades)

wins = (
    closed["result"] == "WIN"
).sum()

losses = (
    closed["result"] == "LOSS"
).sum()


# ============================================================
# WIN RATE
# ============================================================

if closed_count > 0:

    win_rate = (
        wins / closed_count
    ) * 100

else:

    win_rate = 0


# ============================================================
# PROFIT FACTOR
# ============================================================

gross_profit = closed.loc[
    closed["r_multiple"] > 0,
    "r_multiple"
].sum()

gross_loss = abs(
    closed.loc[
        closed["r_multiple"] < 0,
        "r_multiple"
    ].sum()
)

if gross_loss > 0:

    profit_factor = (
        gross_profit
        / gross_loss
    )

else:

    profit_factor = np.inf


# ============================================================
# NET R
# ============================================================

net_r = closed[
    "r_multiple"
].sum()


# ============================================================
# EXPECTANCY
# ============================================================

if closed_count > 0:

    expectancy = (
        net_r
        / closed_count
    )

else:

    expectancy = 0


# ============================================================
# EQUITY / DRAWDOWN
# ============================================================

if closed_count > 0:

    equity = closed[
        "r_multiple"
    ].cumsum()

    running_max = equity.cummax()

    drawdown = (
        equity
        - running_max
    )

    max_drawdown = drawdown.min()

else:

    max_drawdown = 0


# ============================================================
# MAX CONSECUTIVE LOSSES
# ============================================================

max_consecutive_losses = 0

current_losses = 0

for result in closed["result"]:

    if result == "LOSS":

        current_losses += 1

        max_consecutive_losses = max(
            max_consecutive_losses,
            current_losses
        )

    else:

        current_losses = 0


# ============================================================
# PRINT SUMMARY
# ============================================================

print("\n")
print("=" * 70)
print("V1 BACKTEST RESULTS")
print("=" * 70)

print(
    f"Total signals        : {total_signals}"
)

print(
    f"Closed trades        : {closed_count}"
)

print(
    f"Open trades          : {open_count}"
)

print(
    f"Winners              : {wins}"
)

print(
    f"Losers               : {losses}"
)

print(
    f"Win rate             : {win_rate:.2f}%"
)

if np.isinf(profit_factor):

    print(
        "Profit factor       : INF"
    )

else:

    print(
        f"Profit factor       : {profit_factor:.2f}"
    )

print(
    f"Net R                : {net_r:.2f}R"
)

print(
    f"Expectancy           : {expectancy:.3f}R"
)

print(
    f"Max drawdown         : {max_drawdown:.2f}R"
)

print(
    f"Max consecutive loss : {max_consecutive_losses}"
)


# ============================================================
# SESSION BREAKDOWN
# ============================================================

print("\n")
print("=" * 70)
print("SESSION BREAKDOWN")
print("=" * 70)

for session_name in [
    "MORNING",
    "US_OPEN"
]:

    session_trades = closed[
        closed["session"]
        == session_name
    ]

    if len(session_trades) == 0:

        print(
            f"{session_name:10s} : "
            "No closed trades"
        )

        continue

    session_wins = (
        session_trades["result"]
        == "WIN"
    ).sum()

    session_losses = (
        session_trades["result"]
        == "LOSS"
    ).sum()

    session_wr = (
        session_wins
        / len(session_trades)
    ) * 100

    session_r = session_trades[
        "r_multiple"
    ].sum()

    print(
        f"{session_name:10s} : "
        f"Trades={len(session_trades):4d} | "
        f"WinRate={session_wr:6.2f}% | "
        f"NetR={session_r:8.2f}R"
    )


# ============================================================
# LEVEL BREAKDOWN
# ============================================================

print("\n")
print("=" * 70)
print("LEVEL BREAKDOWN")
print("=" * 70)

for level_name in [
    "VAH",
    "POC",
    "VAL"
]:

    level_trades = closed[
        closed["level"]
        == level_name
    ]

    if len(level_trades) == 0:

        print(
            f"{level_name:5s} : "
            "No closed trades"
        )

        continue

    level_wins = (
        level_trades["result"]
        == "WIN"
    ).sum()

    level_wr = (
        level_wins
        / len(level_trades)
    ) * 100

    level_r = level_trades[
        "r_multiple"
    ].sum()

    print(
        f"{level_name:5s} : "
        f"Trades={len(level_trades):4d} | "
        f"WinRate={level_wr:6.2f}% | "
        f"NetR={level_r:8.2f}R"
    )


# ============================================================
# DIRECTION BREAKDOWN
# ============================================================

print("\n")
print("=" * 70)
print("DIRECTION BREAKDOWN")
print("=" * 70)

for direction in [
    "BUY",
    "SELL"
]:

    direction_trades = closed[
        closed["direction"]
        == direction
    ]

    if len(direction_trades) == 0:

        print(
            f"{direction:5s} : "
            "No closed trades"
        )

        continue

    direction_wins = (
        direction_trades["result"]
        == "WIN"
    ).sum()

    direction_wr = (
        direction_wins
        / len(direction_trades)
    ) * 100

    direction_r = direction_trades[
        "r_multiple"
    ].sum()

    print(
        f"{direction:5s} : "
        f"Trades={len(direction_trades):4d} | "
        f"WinRate={direction_wr:6.2f}% | "
        f"NetR={direction_r:8.2f}R"
    )


# ============================================================
# FINAL
# ============================================================

print("\n")
print("=" * 70)

print(
    f"Trades saved to: {OUTPUT_FILE}"
)

print("=" * 70)