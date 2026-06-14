"""Generate a labelled dataset for stockout-risk prediction.

Each sample is a product described by its current stock, demand level and
variability, and lead time. We then *simulate* the coming lead-time window of
daily demand and label the sample ``1`` if the product runs out before the
replenishment arrives. The label therefore has a genuine, noisy relationship
with the features (it is not a hand-written rule), which is exactly what makes
it a real learning problem.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ml.features import FEATURES, TARGET, days_of_cover


def make_dataset(n: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Return a DataFrame with the FEATURES columns plus the TARGET label."""
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        avg = rng.uniform(2, 40)                       # average daily demand
        cv = rng.uniform(0.1, 0.8)                     # coefficient of variation
        std = avg * cv
        lead = int(rng.integers(2, 15))               # replenishment lead time
        # current stock expressed as a random number of "cover days"
        cover_days = rng.uniform(0, 25)
        current_stock = cover_days * avg

        # Simulate demand during the lead-time window.
        demand = rng.normal(avg, std, size=lead).clip(min=0)
        stockout = int(demand.sum() > current_stock)

        rows.append(
            {
                "current_stock": current_stock,
                "avg_daily_demand": avg,
                "demand_std": std,
                "days_of_cover": days_of_cover(current_stock, avg),
                "lead_time_days": float(lead),
                TARGET: stockout,
            }
        )
    df = pd.DataFrame(rows)
    return df[FEATURES + [TARGET]]


if __name__ == "__main__":
    df = make_dataset()
    print(f"{len(df)} samples, stockout rate = {df[TARGET].mean():.1%}")
    print(df.head())
