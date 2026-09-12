import numpy as np
import pandas as pd


def calculate_volume_profile(
    df,
    price_low=None,
    price_high=None,
    num_bins=100,
    value_area_percent=0.70
):
    """
    Calculate a Fixed Range Volume Profile.

    Parameters
    ----------
    df : DataFrame
        Must contain:
        high, low, close, tick_volume

    price_low : float, optional
        Lower boundary of profile.

    price_high : float, optional
        Upper boundary of profile.

    num_bins : int
        Number of price bins.

    value_area_percent : float
        Percentage of volume included in Value Area.
        Default = 70%.

    Returns
    -------
    dict
        POC, VAH, VAL and profile data.
    """

    required_columns = [
        "high",
        "low",
        "close",
        "tick_volume"
    ]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(
                f"Missing required column: {col}"
            )

    data = df[
        required_columns
    ].dropna().copy()

    if data.empty:
        return None

    # --------------------------------------------------
    # Determine price range
    # --------------------------------------------------

    if price_low is None:
        price_low = float(data["low"].min())

    if price_high is None:
        price_high = float(data["high"].max())

    if price_high <= price_low:
        return None

    # --------------------------------------------------
    # Create price bins
    # --------------------------------------------------

    bin_edges = np.linspace(
        price_low,
        price_high,
        num_bins + 1
    )

    volume_profile = np.zeros(
        num_bins,
        dtype=float
    )

    # --------------------------------------------------
    # Distribute candle volume
    # --------------------------------------------------

    for _, row in data.iterrows():

        candle_low = float(row["low"])
        candle_high = float(row["high"])
        candle_volume = float(row["tick_volume"])

        if candle_high <= candle_low:
            continue

        # Find overlapping bins
        start_bin = np.searchsorted(
            bin_edges,
            candle_low,
            side="right"
        ) - 1

        end_bin = np.searchsorted(
            bin_edges,
            candle_high,
            side="left"
        )

        start_bin = max(
            0,
            min(start_bin, num_bins - 1)
        )

        end_bin = max(
            0,
            min(end_bin, num_bins)
        )

        touched_bins = []

        for i in range(
            start_bin,
            end_bin
        ):

            bin_low = bin_edges[i]
            bin_high = bin_edges[i + 1]

            overlap_low = max(
                candle_low,
                bin_low
            )

            overlap_high = min(
                candle_high,
                bin_high
            )

            overlap = max(
                0,
                overlap_high - overlap_low
            )

            if overlap > 0:
                touched_bins.append(
                    (i, overlap)
                )

        # If candle range doesn't overlap
        # due to precision, assign volume
        # to the closest bin.
        if not touched_bins:

            close_price = float(
                row["close"]
            )

            idx = np.searchsorted(
                bin_edges,
                close_price
            ) - 1

            idx = max(
                0,
                min(idx, num_bins - 1)
            )

            volume_profile[idx] += candle_volume

        else:

            total_overlap = sum(
                overlap
                for _, overlap in touched_bins
            )

            if total_overlap <= 0:
                continue

            for idx, overlap in touched_bins:

                volume_profile[idx] += (
                    candle_volume
                    * overlap
                    / total_overlap
                )

    # --------------------------------------------------
    # POC
    # --------------------------------------------------

    poc_index = int(
        np.argmax(volume_profile)
    )

    poc = (
        bin_edges[poc_index]
        + bin_edges[poc_index + 1]
    ) / 2

    # --------------------------------------------------
    # Value Area
    # --------------------------------------------------

    total_volume = volume_profile.sum()

    if total_volume <= 0:
        return None

    target_volume = (
        total_volume
        * value_area_percent
    )

    # Start Value Area from POC
    lower_index = poc_index
    upper_index = poc_index

    accumulated_volume = volume_profile[
        poc_index
    ]

    while accumulated_volume < target_volume:

        next_lower = (
            volume_profile[lower_index - 1]
            if lower_index > 0
            else -1
        )

        next_upper = (
            volume_profile[upper_index + 1]
            if upper_index < num_bins - 1
            else -1
        )

        if next_lower < 0 and next_upper < 0:
            break

        if next_upper > next_lower:

            upper_index += 1

            accumulated_volume += (
                volume_profile[upper_index]
            )

        else:

            lower_index -= 1

            accumulated_volume += (
                volume_profile[lower_index]
            )

    # --------------------------------------------------
    # VAL / VAH
    # --------------------------------------------------

    val = bin_edges[lower_index]

    vah = bin_edges[upper_index + 1]

    # --------------------------------------------------
    # Return result
    # --------------------------------------------------

    profile_df = pd.DataFrame({
        "price_low": bin_edges[:-1],
        "price_high": bin_edges[1:],
        "price": (
            bin_edges[:-1]
            + bin_edges[1:]
        ) / 2,
        "volume": volume_profile
    })

    return {
        "POC": poc,
        "VAH": vah,
        "VAL": val,
        "total_volume": total_volume,
        "profile": profile_df
    }