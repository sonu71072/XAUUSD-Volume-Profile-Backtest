from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# V3 TRANSACTION COST MODEL
# ============================================================
# Purpose:
# Evaluate the existing V2 trade results after applying
# hypothetical spread, commission and slippage assumptions.
#
# IMPORTANT:
# These are research scenarios, not broker-specific costs.
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRADES_FILE = PROJECT_ROOT / "data" / "trades_v2.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "trades_v3_costs.csv"


# ------------------------------------------------------------
# Cost scenarios
# ------------------------------------------------------------
#
# spread_points:
#   Total spread cost expressed in XAUUSD price units.
#
# commission_R:
#   Commission expressed directly as R per completed trade.
#
# slippage_points:
#   Total entry/exit slippage expressed in XAUUSD price units.
#
# These values are deliberately treated as hypothetical
# sensitivity scenarios until broker-specific execution data
# is available.
# ------------------------------------------------------------

SCENARIOS = {
    "BASELINE": {
        "spread_points": 0.00,
        "commission_R": 0.00,
        "slippage_points": 0.00,
    },
    "LOW_COST": {
        "spread_points": 0.10,
        "commission_R": 0.02,
        "slippage_points": 0.05,
    },
    "MEDIUM_COST": {
        "spread_points": 0.20,
        "commission_R": 0.04,
        "slippage_points": 0.10,
    },
    "HIGH_COST": {
        "spread_points": 0.40,
        "commission_R": 0.08,
        "slippage_points": 0.20,
    },
}


def load_trades():
    if not TRADES_FILE.exists():
        raise FileNotFoundError(
            f"Trade file not found: {TRADES_FILE}"
        )

    df = pd.read_csv(TRADES_FILE)

    required_columns = {
        "signal_time",
        "entry_time",
        "exit_time",
        "session_date",
        "session",
        "direction",
        "level",
        "entry",
        "sl",
        "tp",
        "exit",
        "exit_reason",
        "pnl_R",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    return df


def calculate_cost_r(row, scenario):
    """
    Convert hypothetical price costs into R.

    Risk distance is based on the original V2 entry-to-SL
    distance.

    This model applies the specified total price cost to the
    trade and additionally subtracts commission_R.

    For a research sensitivity analysis, the price-cost impact
    is calculated as:

        price_cost / initial_risk_distance

    The resulting value is measured in R.
    """

    entry = float(row["entry"])
    sl = float(row["sl"])

    risk_distance = abs(entry - sl)

    if risk_distance <= 0:
        return np.nan

    price_cost = (
        float(scenario["spread_points"])
        + float(scenario["slippage_points"])
    )

    price_cost_R = price_cost / risk_distance

    total_cost_R = (
        price_cost_R
        + float(scenario["commission_R"])
    )

    return total_cost_R


def calculate_metrics(df):
    pnl = df["net_pnl_R"]

    wins = (pnl > 0).sum()
    losses = (pnl < 0).sum()

    gross_profit = pnl[pnl > 0].sum()
    gross_loss = abs(pnl[pnl < 0].sum())

    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    else:
        profit_factor = np.inf

    cumulative = pnl.cumsum()
    running_max = cumulative.cummax()
    drawdown = cumulative - running_max
    max_drawdown = drawdown.min()

    return {
        "Trades": len(df),
        "Winners": int(wins),
        "Losers": int(losses),
        "Win Rate %": (wins / len(df) * 100) if len(df) else 0,
        "Total R": pnl.sum(),
        "Average R": pnl.mean(),
        "Profit Factor": profit_factor,
        "Max Drawdown R": max_drawdown,
        "Total Cost R": df["total_cost_R"].sum(),
    }


def main():
    trades = load_trades()

    results = []
    all_trades = []

    for scenario_name, scenario in SCENARIOS.items():

        scenario_df = trades.copy()

        scenario_df["total_cost_R"] = scenario_df.apply(
            lambda row: calculate_cost_r(row, scenario),
            axis=1,
        )

        scenario_df["net_pnl_R"] = (
            scenario_df["pnl_R"]
            - scenario_df["total_cost_R"]
        )

        scenario_df["scenario"] = scenario_name

        metrics = calculate_metrics(scenario_df)
        metrics["Scenario"] = scenario_name
        metrics["Spread"] = scenario["spread_points"]
        metrics["Commission R"] = scenario["commission_R"]
        metrics["Slippage"] = scenario["slippage_points"]

        results.append(metrics)

        all_trades.append(scenario_df)

    results_df = pd.DataFrame(results)

    # Save trade-level V3 results
    output_df = pd.concat(all_trades, ignore_index=True)

    output_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # Display summary
    print("\n" + "=" * 80)
    print("V3 TRANSACTION COST ANALYSIS")
    print("=" * 80)

    print(
        results_df[
            [
                "Scenario",
                "Trades",
                "Win Rate %",
                "Total R",
                "Average R",
                "Profit Factor",
                "Max Drawdown R",
                "Total Cost R",
            ]
        ].to_string(index=False)
    )

    print("\n" + "=" * 80)
    print(f"Saved: {OUTPUT_FILE}")
    print("=" * 80)


if __name__ == "__main__":
    main()