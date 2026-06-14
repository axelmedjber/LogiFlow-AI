"""KPI computation for stock movements.

All functions take a tidy ``movements`` DataFrame with these columns:

- ``date``           : the movement date (datetime)
- ``product``        : product name (str)
- ``movement_type``  : ``"in"`` (reception) or ``"out"`` (shipment)
- ``quantity``       : units moved (positive int)

Stock is **movement-based**: the stock of a product is the sum of its
incoming quantities minus its outgoing quantities. Nothing is stored as a
mutable counter, so the figures can always be recomputed from history.

This module is pure pandas and has no Streamlit dependency, so it can be
unit-tested on its own.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {"date", "product", "movement_type", "quantity"}
_VALID_TYPES = {"in", "out"}


def load_movements(path: str | Path) -> pd.DataFrame:
    """Load and validate a movements CSV."""
    df = pd.read_csv(path, parse_dates=["date"])
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    bad = set(df["movement_type"].unique()) - _VALID_TYPES
    if bad:
        raise ValueError(f"movement_type must be 'in' or 'out', found: {sorted(bad)}")
    return df


def signed_quantity(df: pd.DataFrame) -> pd.Series:
    """Quantity signed by direction: +qty for receptions, -qty for shipments."""
    sign = df["movement_type"].map({"in": 1, "out": -1})
    return df["quantity"] * sign


def current_stock(df: pd.DataFrame) -> pd.DataFrame:
    """Current stock per product (received minus shipped)."""
    work = df.assign(signed=signed_quantity(df))
    stock = work.groupby("product")["signed"].sum().rename("stock")
    return stock.reset_index().sort_values("product").reset_index(drop=True)


def stock_timeline(df: pd.DataFrame, product: str | None = None) -> pd.DataFrame:
    """Cumulative stock over time, optionally filtered to one product."""
    work = df.assign(signed=signed_quantity(df)).sort_values("date")
    if product is not None:
        work = work[work["product"] == product]
    work["stock"] = work.groupby("product")["signed"].cumsum()
    return work[["date", "product", "stock"]].reset_index(drop=True)


def product_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Per-product received, shipped, current stock and turnover ratio.

    Turnover ratio = total shipped / current stock (how many times the
    on-hand stock has been sold through). Undefined when stock is zero, so
    it is reported as 0.0 there.
    """
    received = (
        df[df["movement_type"] == "in"].groupby("product")["quantity"].sum()
    )
    shipped = (
        df[df["movement_type"] == "out"].groupby("product")["quantity"].sum()
    )
    summary = pd.DataFrame({"received": received, "shipped": shipped}).fillna(0)
    summary["stock"] = summary["received"] - summary["shipped"]
    summary["turnover"] = summary.apply(
        lambda r: round(r["shipped"] / r["stock"], 2) if r["stock"] > 0 else 0.0,
        axis=1,
    )
    return summary.astype(
        {"received": int, "shipped": int, "stock": int}
    ).reset_index()


def stockout_alerts(df: pd.DataFrame, reorder_points: dict[str, int]) -> pd.DataFrame:
    """Products at or below their reorder point.

    ``reorder_points`` maps product name to its reorder threshold.
    """
    stock = current_stock(df).set_index("product")["stock"]
    rows = []
    for product, rop in reorder_points.items():
        level = int(stock.get(product, 0))
        if level <= rop:
            rows.append({"product": product, "stock": level, "reorder_point": rop})
    return pd.DataFrame(rows, columns=["product", "stock", "reorder_point"])


def summary_kpis(df: pd.DataFrame) -> dict:
    """Headline numbers for the dashboard's metric cards."""
    received = int(df.loc[df["movement_type"] == "in", "quantity"].sum())
    shipped = int(df.loc[df["movement_type"] == "out", "quantity"].sum())
    return {
        "products": int(df["product"].nunique()),
        "movements": int(len(df)),
        "total_received": received,
        "total_shipped": shipped,
        "net_stock": received - shipped,
    }
