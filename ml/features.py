"""Feature engineering for stockout-risk prediction.

The model scores each product from a handful of interpretable features that can
be computed either from real stock movements (in the dashboard) or simulated
(for training). Keeping a single feature definition guarantees the training
data and the live data look identical to the model.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# The exact feature order the model is trained on.
FEATURES = [
    "current_stock",
    "avg_daily_demand",
    "demand_std",
    "days_of_cover",
    "lead_time_days",
]
TARGET = "stockout"


def days_of_cover(current_stock: float, avg_daily_demand: float) -> float:
    """How many days the current stock lasts at the average consumption rate."""
    if avg_daily_demand <= 0:
        return float("inf") if current_stock > 0 else 0.0
    return current_stock / avg_daily_demand


def product_features(movements: pd.DataFrame, lead_time_days: int = 5) -> pd.DataFrame:
    """Compute one feature row per product from a movements DataFrame.

    Expects columns: date, product, movement_type ('in'/'out'), quantity.
    """
    df = movements.copy()
    df["date"] = pd.to_datetime(df["date"])
    sign = df["movement_type"].map({"in": 1, "out": -1})
    df["signed"] = df["quantity"] * sign

    rows = []
    for product, g in df.groupby("product"):
        current_stock = float(g["signed"].sum())
        out = g[g["movement_type"] == "out"]
        # Daily outflow series (demand per day).
        daily = out.groupby(out["date"].dt.date)["quantity"].sum()
        n_days = max((df["date"].max() - df["date"].min()).days, 1)
        avg = float(out["quantity"].sum()) / n_days
        std = float(daily.std(ddof=0)) if len(daily) > 1 else 0.0
        rows.append(
            {
                "product": product,
                "current_stock": current_stock,
                "avg_daily_demand": avg,
                "demand_std": std,
                "days_of_cover": days_of_cover(current_stock, avg),
                "lead_time_days": float(lead_time_days),
            }
        )
    out_df = pd.DataFrame(rows).set_index("product")
    # days_of_cover can be inf when there is no demand; cap it for the model.
    out_df["days_of_cover"] = out_df["days_of_cover"].replace(np.inf, 999.0)
    return out_df[FEATURES]
