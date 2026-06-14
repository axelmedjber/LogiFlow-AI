# LogiFlow-AI

An interactive **stock KPI dashboard** for a warehouse or social grocery,
built with [Streamlit](https://streamlit.io/). Feed it your stock movements
(receptions and shipments) and it shows, at a glance:

- headline KPIs (products, movements, total received/shipped, net stock);
- stock evolution over time, per product or all together;
- a per-product table with received / shipped / current stock / turnover;
- automatic **reorder alerts** for products running low.

Stock is **movement-based**: a product's stock is always recomputed as
receptions minus shipments, never stored as a mutable counter.

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app opens in your browser and loads the sample dataset
(`data/stock_movements.csv`, 8 grocery products over 60 days). You can also
upload your own CSV from the sidebar.

> **Deploy a public demo (free):** push this repo to GitHub, go to
> [share.streamlit.io](https://share.streamlit.io), click *New app*, pick the
> repo and set the main file to `app.py`. You get a public URL to share.

## Input format

```csv
date,product,movement_type,quantity
2025-01-01,Riz,in,300
2025-01-08,Riz,out,25
```

`movement_type` is `in` (reception) or `out` (shipment).

## Architecture

The KPI logic lives in `src/kpi.py` (pure pandas, **no Streamlit**), so it is
fully unit-tested independently of the UI. `app.py` is only the presentation
layer on top.

```
LogiFlow-AI/
├── app.py              # Streamlit dashboard (UI)
├── src/
│   └── kpi.py          # KPI computation (pure pandas, tested)
├── data/
│   └── stock_movements.csv
├── tests/              # unit tests (pytest)
└── requirements.txt
```

## Use the KPI layer directly

```python
from src.kpi import load_movements, product_summary, stockout_alerts

df = load_movements("data/stock_movements.csv")
print(product_summary(df))
print(stockout_alerts(df, {"Riz": 120, "Huile": 130}))
```

## Tests

```bash
pytest
```

## License

MIT
