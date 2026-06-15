"""Turn an arbitrary uploaded CSV into the canonical movements format.

Real-world exports rarely use the exact column names the dashboard expects
(`date, product, movement_type, quantity`). This module lets the app map any
columns onto that schema, and normalises types, so the rest of the code always
sees clean data.
"""

from __future__ import annotations

import pandas as pd

REQUIRED = ["date", "product", "movement_type", "quantity"]

# Keyword hints used to pre-select the right column in the mapping UI.
HINTS = {
    "date": ["date", "jour", "day", "time"],
    "product": ["product", "produit", "article", "item", "sku", "ref"],
    "quantity": ["quantity", "quantite", "quantité", "qty", "qte", "nombre", "amount"],
    # Note: avoid the bare "mouv" hint -- it collides with date columns named
    # like "date_mouvement". "movement" (English) does not.
    "movement_type": ["movement", "type", "sens", "direction", "flux"],
}


def guess_column(columns, field: str):
    """Best-guess column name for a canonical field, or None."""
    for col in columns:
        low = str(col).lower()
        if any(k in low for k in HINTS.get(field, [])):
            return col
    return None


def coerce(df: pd.DataFrame) -> pd.DataFrame:
    """Clean a frame that already has the required columns."""
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["product"] = out["product"].astype(str)
    out["quantity"] = pd.to_numeric(out["quantity"], errors="coerce")
    out["movement_type"] = out["movement_type"].astype(str).str.lower().str.strip()
    out = out.dropna(subset=["date", "quantity"])
    out = out[out["movement_type"].isin(["in", "out"])]
    return out[REQUIRED].reset_index(drop=True)


def apply_mapping(
    raw: pd.DataFrame,
    date_col: str,
    product_col: str,
    quantity_col: str,
    type_col: str,
    in_values,
) -> pd.DataFrame:
    """Map arbitrary columns to the canonical schema.

    ``in_values`` is the set of values in ``type_col`` that mean a reception
    ("in"); every other value is treated as a shipment ("out").
    """
    in_values = {str(v) for v in in_values}
    out = pd.DataFrame()
    out["date"] = pd.to_datetime(raw[date_col], errors="coerce")
    out["product"] = raw[product_col].astype(str)
    out["quantity"] = pd.to_numeric(raw[quantity_col], errors="coerce").abs()
    out["movement_type"] = raw[type_col].astype(str).apply(
        lambda v: "in" if v in in_values else "out"
    )
    out = out.dropna(subset=["date", "quantity"])
    out = out[out["quantity"] > 0]
    return out[REQUIRED].reset_index(drop=True)
