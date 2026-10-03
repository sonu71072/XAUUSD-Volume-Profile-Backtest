from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

MARKET_FILE = ROOT / "data" / "XAUUSD_M5.csv"
PROFILES_FILE = ROOT / "data" / "session_profiles_v2.csv"
TRADES_FILE = ROOT / "data" / "trades_v8_oos.csv"

OOS_START = pd.Timestamp("2025-09-12", tz="UTC")
OOS_END = pd.Timestamp("2026-09-12", tz="UTC")

RR = 2.0
BODY_RATIO_MIN = 0.70
POC_DISTANCE_MAX_R = 0.20
TIMEZONE = "Asia/Kolkata"


def check(name, condition):
    status = "PASS" if bool(condition) else "FAIL"
    print(f"[{status}] {name}")
    return bool(condition)


def main():
    trades = pd.read_csv(TRADES_FILE)
    market = pd.read_csv(MARKET_FILE)
    profiles = pd.read_csv(PROFILES_FILE)

    market["time"] = pd.to_datetime(market["time"], utc=True)
    market = market.sort_values("time").reset_index(drop=True)

    trades["signal_time"] = pd.to_datetime(trades["signal_time"], utc=True)
    trades["entry_time"] = pd.to_datetime(trades["entry_time"], utc=True)
    trades["exit_time"] = pd.to_datetime(trades["exit_time"], utc=True)

    profiles["session_date"] = pd.to_datetime(
        profiles["session_date"], errors="coerce"
    ).dt.date
    profiles["profile_date"] = pd.to_datetime(
        profiles["profile_date"], errors="coerce"
    ).dt.date

    print("=" * 70)
    print("V8 OUT-OF-SAMPLE STRUCTURAL VALIDATION")
    print("=" * 70)

    print(f"Trades   : {len(trades)}")
    print(f"Profiles : {len(profiles)}")
    print(f"Market   : {len(market)}")

    results = []

    results.append(check(
        "trade_count_positive",
        len(trades) > 0
    ))

    results.append(check(
        "all_trades_inside_oos_period",
        (
            (trades["signal_time"] >= OOS_START) &
            (trades["signal_time"] < OOS_END) &
            (trades["entry_time"] >= OOS_START) &
            (trades["entry_time"] < OOS_END) &
            (trades["exit_time"] >= OOS_START) &
            (trades["exit_time"] < OOS_END)
        ).all()
    ))

    # --------------------------------------------------------
    # Profile checks
    # --------------------------------------------------------

    profile_before = []
    profile_found = []
    profile_matches_source = []

    for _, t in trades.iterrows():
        session_date = pd.Timestamp(t["session_date"]).date()
        session = t["session"]
        profile_date = pd.Timestamp(t["profile_date"]).date()

        profile_before.append(profile_date < session_date)

        match = profiles[
            (profiles["session_date"] == session_date) &
            (profiles["session"] == session)
        ]

        profile_found.append(len(match) > 0)

        if len(match) > 0:
            source_date = match.iloc[0]["profile_date"]
            profile_matches_source.append(
                pd.Timestamp(source_date).date() == profile_date
            )
        else:
            profile_matches_source.append(False)

    results.append(check(
        "profile_before_session",
        all(profile_before)
    ))
    print(f"Valid previous profiles: {sum(profile_before)}/{len(profile_before)}")

    results.append(check(
        "all_profiles_found",
        all(profile_found)
    ))
    print(f"Valid profiles found: {sum(profile_found)}/{len(profile_found)}")

    results.append(check(
        "profile_date_matches_source",
        all(profile_matches_source)
    ))

    # --------------------------------------------------------
    # Execution checks
    # --------------------------------------------------------

    delays = (
        trades["entry_time"] - trades["signal_time"]
    ).dt.total_seconds() / 60.0

    results.append(check(
        "entry_after_signal",
        (delays > 0).all()
    ))

    print(
        f"Entry delay min/max/mean: "
        f"{delays.min():.2f} / {delays.max():.2f} / {delays.mean():.2f} min"
    )

    results.append(check(
        "entry_delay_exactly_5min",
        np.allclose(delays, 5.0, atol=1e-9)
    ))

    session_counts = (
        trades.groupby(["session_date", "session"])
        .size()
    )

    results.append(check(
        "one_trade_per_session",
        (session_counts <= 1).all()
    ))

    print(
        f"Sessions with >1 trade: "
        f"{int((session_counts > 1).sum())}"
    )

    # --------------------------------------------------------
    # RR checks
    # --------------------------------------------------------

    tp_mask = trades["exit_reason"].eq("TP")
    sl_mask = trades["exit_reason"].eq("SL")

    tp_r_ok = np.isclose(
        trades.loc[tp_mask, "pnl_R"].to_numpy(),
        RR,
        atol=1e-9
    ).all()

    sl_r_ok = np.isclose(
        trades.loc[sl_mask, "pnl_R"].to_numpy(),
        -1.0,
        atol=1e-9
    ).all()

    results.append(check("tp_equals_2R", tp_r_ok))
    print(f"TP trades: {int(tp_mask.sum())}")

    results.append(check("sl_equals_minus_1R", sl_r_ok))
    print(f"SL trades: {int(sl_mask.sum())}")

    results.append(check(
        "exit_after_entry",
        (trades["exit_time"] >= trades["entry_time"]).all()
    ))

    same_candle = (
        trades["exit_time"] == trades["entry_time"]
    ).sum()
    print(f"Same-candle exits: {int(same_candle)}")

    results.append(check(
        "valid_exit_reasons",
        trades["exit_reason"].isin(["SL", "TP"]).all()
    ))
    print(
        f"Exit reasons: "
        f"{sorted(trades['exit_reason'].dropna().unique().tolist())}"
    )

    # --------------------------------------------------------
    # PnL consistency
    # --------------------------------------------------------

    risk = abs(trades["entry"] - trades["sl"])

    expected_r = np.where(
        trades["direction"].eq("BUY"),
        (trades["exit"] - trades["entry"]) / risk,
        (trades["entry"] - trades["exit"]) / risk,
    )

    pnl_diff = np.max(
        np.abs(expected_r - trades["pnl_R"])
    )

    results.append(check(
        "pnl_consistency",
        np.allclose(
            expected_r,
            trades["pnl_R"].to_numpy(),
            atol=1e-9
        )
    ))
    print(f"Max R calculation difference: {pnl_diff:.12f}")

    # --------------------------------------------------------
    # Body ratio
    # --------------------------------------------------------

    results.append(check(
        "body_ratio_present",
        trades["body_ratio"].notna().all()
    ))

    results.append(check(
        "body_ratio_filter_70pct",
        (trades["body_ratio"] >= BODY_RATIO_MIN).all()
    ))

    print(
        f"Body ratio min/max/mean: "
        f"{trades['body_ratio'].min():.6f} / "
        f"{trades['body_ratio'].max():.6f} / "
        f"{trades['body_ratio'].mean():.6f}"
    )

    # Recalculate body ratio from source candle.
    body_diffs = []

    for _, t in trades.iterrows():
        matches = market[market["time"] == t["signal_time"]]

        if len(matches) != 1:
            body_diffs.append(np.inf)
            continue

        bar = matches.iloc[0]
        candle_range = float(bar["high"] - bar["low"])

        if candle_range <= 0:
            body_diffs.append(np.inf)
            continue

        calculated = abs(
            float(bar["close"] - bar["open"])
        ) / candle_range

        body_diffs.append(
            abs(calculated - float(t["body_ratio"]))
        )

    max_body_diff = max(body_diffs) if body_diffs else np.inf

    results.append(check(
        "body_ratio_calculation_consistent",
        max_body_diff <= 1e-9
    ))

    print(
        f"Body ratio calculation difference: "
        f"{max_body_diff:.12f}"
    )

    # --------------------------------------------------------
    # V8 POC distance filter
    # --------------------------------------------------------

    calculated_distance = (
        abs(trades["entry"] - trades["level_price"]) /
        abs(trades["entry"] - trades["sl"])
    )

    stored_distance_diff = np.max(
        np.abs(
            calculated_distance -
            trades["distance_risk"]
        )
    )

    results.append(check(
        "poc_distance_calculation_consistent",
        np.allclose(
            calculated_distance,
            trades["distance_risk"].to_numpy(),
            atol=1e-9
        )
    ))

    results.append(check(
        "poc_distance_filter_20pct",
        (trades["distance_risk"] <= POC_DISTANCE_MAX_R + 1e-12).all()
    ))

    print(
        f"POC distance R min/max/mean: "
        f"{trades['distance_risk'].min():.6f} / "
        f"{trades['distance_risk'].max():.6f} / "
        f"{trades['distance_risk'].mean():.6f}"
    )

    print(
        f"POC distance calculation difference: "
        f"{stored_distance_diff:.12f}"
    )

    # --------------------------------------------------------
    # Timeline checks
    # --------------------------------------------------------

    results.append(check(
        "signal_before_or_at_entry",
        (trades["signal_time"] <= trades["entry_time"]).all()
    ))

    results.append(check(
        "entry_before_or_at_exit",
        (trades["entry_time"] <= trades["exit_time"]).all()
    ))

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("FINAL V8 OOS VALIDATION SUMMARY")
    print("=" * 70)

    names = [
        "trade_count_positive",
        "all_trades_inside_oos_period",
        "profile_before_session",
        "all_profiles_found",
        "profile_date_matches_source",
        "entry_after_signal",
        "entry_delay_exactly_5min",
        "one_trade_per_session",
        "tp_equals_2R",
        "sl_equals_minus_1R",
        "exit_after_entry",
        "valid_exit_reasons",
        "pnl_consistency",
        "body_ratio_present",
        "body_ratio_filter_70pct",
        "body_ratio_calculation_consistent",
        "poc_distance_calculation_consistent",
        "poc_distance_filter_20pct",
        "signal_before_or_at_entry",
        "entry_before_or_at_exit",
    ]

    for name, passed in zip(names, results):
        print(f"{'PASS' if passed else 'FAIL'} | {name}")

    print()

    if all(results):
        print("V8 OOS STRUCTURAL VALIDATION: PASSED")
        print(
            "All OOS period, causal profile, execution, RR, "
            "PnL, body-ratio and POC-distance validation checks passed."
        )
        raise SystemExit(0)

    print("V8 OOS STRUCTURAL VALIDATION: FAILED")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
