# LogiFlow-AI

An interactive **stock KPI dashboard** for a warehouse or social grocery,
built with [Streamlit](https://streamlit.io/). Feed it your stock movements
(receptions and shipments) and it shows, at a glance:

- headline KPIs (products, movements, total received/shipped, net stock);
- stock evolution over time, per product or all together;
- a per-product table with received / shipped / current stock / turnover;
- automatic **reorder alerts** for products running low;
- a **machine-learning stockout-risk score** for every product (see below).

Stock is **movement-based**: a product's stock is always recomputed as
receptions minus shipments, never stored as a mutable counter.

## Machine learning: stockout-risk prediction

A **gradient-boosting classifier** (scikit-learn) estimates the probability
that each product runs out before its next delivery, from its current stock,
demand level, demand variability and lead time. Because the model is small it
loads directly inside the dashboard — the risk table updates live.

The model is trained on simulated products whose stockout label comes from
*simulating* the lead-time demand window (a genuine, noisy learning problem,
not a hand-written rule). Held-out test performance:

| Metric | Score |
| --- | --- |
| Accuracy | 0.97 |
| ROC-AUC | 0.99 |

Retrain it (and re-export `models/stockout_model.pkl`) with:

```bash
pip install -r requirements.txt
python -m ml.train
```

`ml/features.py` defines the features once, so the dashboard scores live
products with exactly the same inputs the model was trained on.

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
