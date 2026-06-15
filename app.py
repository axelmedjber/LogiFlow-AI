"""LogiFlow-AI -- a Streamlit dashboard for warehouse stock KPIs.

Run it with:

    streamlit run app.py

It reads stock movements (receptions and shipments), then shows headline
KPIs, stock evolution over time, a per-product table, and reorder alerts.
The numbers all come from src/kpi.py, which is unit-tested separately.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.kpi import (
    load_movements,
    current_stock,
    stock_timeline,
    product_summary,
    stockout_alerts,
    summary_kpis,
)
from ml.features import product_features
from src.ingest import REQUIRED, apply_mapping, coerce, guess_column

DATA_FILE = Path(__file__).resolve().parent / "data" / "stock_movements.csv"
MODEL_FILE = Path(__file__).resolve().parent / "models" / "stockout_model.pkl"

st.set_page_config(page_title="LogiFlow-AI", page_icon="📦", layout="wide")
st.title("📦 LogiFlow-AI — Warehouse KPI Dashboard")

# --- Data source ---------------------------------------------------------
uploaded = st.sidebar.file_uploader(
    "Upload a movements CSV (date, product, movement_type, quantity)",
    type="csv",
)
with open(DATA_FILE, "rb") as _f:
    st.sidebar.download_button(
        "⬇️ Download template / sample CSV",
        _f.read(),
        file_name="movements_template.csv",
        mime="text/csv",
        help="Columns: date, product, movement_type ('in'/'out'), quantity.",
    )
if uploaded is None:
    df = load_movements(DATA_FILE)
else:
    try:
        raw = pd.read_csv(uploaded)
    except Exception as exc:
        st.error(f"Could not read this file as CSV: {exc}")
        st.stop()

    if set(REQUIRED).issubset(raw.columns):
        df = coerce(raw)
    else:
        # The columns don't match -> let the user map them.
        st.warning(
            "Your CSV columns don't match the expected format. "
            "Map them below to use your own data."
        )
        cols = list(raw.columns)

        def _idx(field):
            g = guess_column(cols, field)
            return cols.index(g) if g in cols else 0

        m1, m2 = st.columns(2)
        date_col = m1.selectbox("Date column", cols, index=_idx("date"))
        product_col = m2.selectbox("Product column", cols, index=_idx("product"))
        qty_col = m1.selectbox("Quantity column", cols, index=_idx("quantity"))
        type_col = m2.selectbox("Movement-type column", cols, index=_idx("movement_type"))

        type_values = sorted(raw[type_col].astype(str).unique())
        default_in = [
            v for v in type_values
            if any(k in v.lower() for k in ["in", "rec", "entr", "+", "achat"])
        ]
        in_values = st.multiselect(
            "Which value(s) mean a RECEPTION (stock in)?",
            type_values,
            default=default_in,
        )
        if not in_values:
            st.info("Select which value(s) mean a reception to continue.")
            st.stop()

        df = apply_mapping(raw, date_col, product_col, qty_col, type_col, in_values)

    if df.empty:
        st.error("No valid rows after parsing — check your column mapping.")
        st.stop()

period = f"{df['date'].min():%Y-%m-%d} → {df['date'].max():%Y-%m-%d}"
st.caption(f"Period: {period}")

# --- Headline KPIs -------------------------------------------------------
kpis = summary_kpis(df)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Products", kpis["products"])
c2.metric("Movements", kpis["movements"])
c3.metric("Received", f"{kpis['total_received']:,}")
c4.metric("Shipped", f"{kpis['total_shipped']:,}")
c5.metric("Net stock", f"{kpis['net_stock']:,}")

st.divider()

# --- Stock over time -----------------------------------------------------
left, right = st.columns([2, 1])

with left:
    st.subheader("Stock over time")
    products = sorted(df["product"].unique())
    chosen = st.selectbox("Product", ["All products"] + products)
    if chosen == "All products":
        timeline = stock_timeline(df)
        chart = timeline.pivot_table(
            index="date", columns="product", values="stock", aggfunc="last"
        ).ffill()
    else:
        timeline = stock_timeline(df, product=chosen)
        chart = timeline.set_index("date")["stock"]
    st.line_chart(chart)

with right:
    st.subheader("Current stock")
    stock = current_stock(df).set_index("product")["stock"]
    st.bar_chart(stock)

st.divider()

# --- Per-product table + alerts -----------------------------------------
st.subheader("Per-product summary")
st.dataframe(product_summary(df), width="stretch", hide_index=True)

st.subheader("Reorder alerts")
# Simple reorder rule for the demo: alert when stock <= 20% of total received.
summary = product_summary(df).set_index("product")
reorder_points = {p: int(0.2 * summary.loc[p, "received"]) for p in summary.index}
alerts = stockout_alerts(df, reorder_points)
if alerts.empty:
    st.success("No product is below its reorder point.")
else:
    st.warning(f"{len(alerts)} product(s) need restocking:")
    st.dataframe(alerts, width="stretch", hide_index=True)

st.divider()

# --- Machine-learning stockout risk -------------------------------------
st.subheader("🤖 Stockout risk (machine learning)")
st.caption(
    "A gradient-boosting model (scikit-learn) estimates the probability that "
    "each product runs out before its next delivery, from its stock, demand "
    "level, demand variability and lead time."
)

lead_time = st.slider("Assumed lead time (days)", 2, 15, 5)

if not MODEL_FILE.exists():
    st.info("Trained model not found. Run `python -m ml.train` to create it.")
else:
    import joblib

    model = joblib.load(MODEL_FILE)
    feats = product_features(df, lead_time_days=lead_time)
    risk = model.predict_proba(feats)[:, 1]

    out = feats.copy()
    out["stockout_risk"] = (risk * 100).round(0)
    out = out.reset_index().sort_values("stockout_risk", ascending=False)
    out["stockout_risk"] = out["stockout_risk"].astype(int).astype(str) + " %"

    show = out[
        ["product", "current_stock", "avg_daily_demand", "days_of_cover", "stockout_risk"]
    ].round(1)
    st.dataframe(show, width="stretch", hide_index=True)

    high = int((risk >= 0.5).sum())
    if high:
        st.error(f"⚠️ {high} product(s) are at high risk of stockout (≥ 50%).")
    else:
        st.success("No product is at high risk of stockout.")
