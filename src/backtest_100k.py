import os
import pandas as pd
import numpy as np


# ============================================================
# CONFIG
# ============================================================

TRADE_FILE = "data/trades_v1.csv"

STARTING_BALANCE = 100000.0

RISK_PERCENT = 1.0

RR = 2.0

OUTPUT_FILE = "results/backtest_100k.csv"


# ============================================================
# HEADER
# ============================================================

print("=" * 100)
print("$100,000 XAUUSD V1 BACKTEST")
print("=" * 100)


# ============================================================
# LOAD
# ============================================================

print("\nLoading trades...")

trades = pd.read_csv(TRADE_FILE)

trades = trades[
    trades["result"].isin(["WIN", "LOSS"])
].copy()

trades["entry_time"] = pd.to_datetime(
    trades["entry_time"]
)

trades = trades.sort_values(
    "entry_time"
).reset_index(drop=True)

print(f"Closed trades : {len(trades):,}")


# ============================================================
# ACCOUNT
# ============================================================

balance = STARTING_BALANCE

peak_balance = STARTING_BALANCE

max_drawdown = 0.0

wins = 0
losses = 0

equity = []

total_pnl = 0.0


# ============================================================
# TRADE SIMULATION
# ============================================================

print("\nRunning $100K simulation...\n")

print(
    f"{'#':>4} "
    f"{'Date':<12} "
    f"{'Session':<10} "
    f"{'Dir':<5} "
    f"{'Level':<5} "
    f"{'Result':<7} "
    f"{'Risk $':>12} "
    f"{'P&L $':>14} "
    f"{'Balance $':>16}"
)

print("-" * 100)


for i, trade in trades.iterrows():

    # --------------------------------------------------------
    # Risk amount
    # --------------------------------------------------------

    risk_amount = (
        balance
        * RISK_PERCENT
        / 100
    )

    # --------------------------------------------------------
    # P&L
    # --------------------------------------------------------

    if trade["result"] == "WIN":

        pnl = (
            risk_amount
            * RR
        )

        wins += 1

    else:

        pnl = -risk_amount

        losses += 1

    # --------------------------------------------------------
    # Balance
    # --------------------------------------------------------

    balance += pnl

    total_pnl += pnl

    # --------------------------------------------------------
    # Drawdown
    # --------------------------------------------------------

    if balance > peak_balance:

        peak_balance = balance

    current_drawdown = (
        balance
        - peak_balance
    )

    if current_drawdown < max_drawdown:

        max_drawdown = current_drawdown

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    equity.append({

        "trade_number":
            i + 1,

        "date":
            trade["date"],

        "session":
            trade["session"],

        "direction":
            trade["direction"],

        "level":
            trade["level"],

        "result":
            trade["result"],

        "entry_price":
            trade["entry_price"],

        "stop_loss":
            trade["stop_loss"],

        "take_profit":
            trade["take_profit"],

        "risk_amount":
            risk_amount,

        "pnl":
            pnl,

        "balance":
            balance,

        "drawdown":
            current_drawdown
    })

    # --------------------------------------------------------
    # PRINT EVERY TRADE
    # --------------------------------------------------------

    print(
        f"{i + 1:>4} "
        f"{str(trade['date']):<12} "
        f"{str(trade['session']):<10} "
        f"{str(trade['direction']):<5} "
        f"{str(trade['level']):<5} "
        f"{str(trade['result']):<7} "
        f"${risk_amount:>11,.2f} "
        f"${pnl:>13,.2f} "
        f"${balance:>15,.2f}"
    )


# ============================================================
# DATAFRAME
# ============================================================

equity_df = pd.DataFrame(equity)


# ============================================================
# METRICS
# ============================================================

total_trades = len(equity_df)

win_rate = (
    wins
    / total_trades
) * 100

final_balance = balance

total_profit = (
    final_balance
    - STARTING_BALANCE
)

return_percent = (
    total_profit
    / STARTING_BALANCE
) * 100


# ============================================================
# PROFIT FACTOR
# ============================================================

gross_profit = equity_df.loc[
    equity_df["pnl"] > 0,
    "pnl"
].sum()

gross_loss = abs(
    equity_df.loc[
        equity_df["pnl"] < 0,
        "pnl"
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
# MAX CONSECUTIVE LOSSES
# ============================================================

max_loss_streak = 0

current_loss_streak = 0

for result in equity_df["result"]:

    if result == "LOSS":

        current_loss_streak += 1

        max_loss_streak = max(
            max_loss_streak,
            current_loss_streak
        )

    else:

        current_loss_streak = 0


# ============================================================
# SAVE
# ============================================================

os.makedirs(
    "results",
    exist_ok=True
)

equity_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# FINAL REPORT
# ============================================================

print("\n")
print("=" * 100)
print("FINAL $100,000 BACKTEST RESULT")
print("=" * 100)

print(
    f"Starting Capital       : "
    f"${STARTING_BALANCE:,.2f}"
)

print(
    f"Risk per Trade         : "
    f"{RISK_PERCENT:.2f}%"
)

print(
    f"Total Trades           : "
    f"{total_trades:,}"
)

print(
    f"Winners                : "
    f"{wins:,}"
)

print(
    f"Losers                 : "
    f"{losses:,}"
)

print(
    f"Win Rate               : "
    f"{win_rate:.2f}%"
)

print(
    f"Gross Profit           : "
    f"${gross_profit:,.2f}"
)

print(
    f"Gross Loss             : "
    f"${gross_loss:,.2f}"
)

print(
    f"Profit Factor          : "
    f"{profit_factor:.2f}"
)

print(
    f"Total P&L              : "
    f"${total_profit:,.2f}"
)

print(
    f"Final Balance          : "
    f"${final_balance:,.2f}"
)

print(
    f"Total Return           : "
    f"{return_percent:.2f}%"
)

print(
    f"Max Drawdown           : "
    f"${max_drawdown:,.2f}"
)

print(
    f"Max Loss Streak        : "
    f"{max_loss_streak}"
)

print("=" * 100)

print(
    f"\nDetailed trade P&L saved to:"
)

print(
    OUTPUT_FILE
)

print("=" * 100)