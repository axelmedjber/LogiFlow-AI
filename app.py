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

DATA_FILE = Path(__file__).resolve().parent / "data" / "stock_movements.csv"

st.set_page_config(page_title="LogiFlow-AI", page_icon="📦", layout="wide")
st.title("📦 LogiFlow-AI — Warehouse KPI Dashboard")

# --- Data source ---------------------------------------------------------
uploaded = st.sidebar.file_uploader(
    "Upload a movements CSV (date, product, movement_type, quantity)",
    type="csv",
)
source = uploaded if uploaded is not None else DATA_FILE
df = load_movements(source)

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
