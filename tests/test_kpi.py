import pandas as pd
import pytest

from src.kpi import (
    signed_quantity,
    current_stock,
    stock_timeline,
    product_summary,
    stockout_alerts,
    summary_kpis,
)


def sample() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"]
            ),
            "product": ["Rice", "Rice", "Pasta", "Rice"],
            "movement_type": ["in", "out", "in", "out"],
            "quantity": [100, 30, 50, 20],
        }
    )


def test_signed_quantity_signs_by_direction():
    s = signed_quantity(sample())
    assert s.tolist() == [100, -30, 50, -20]


def test_current_stock_is_in_minus_out():
    stock = current_stock(sample()).set_index("product")["stock"]
    assert stock["Rice"] == 50  # 100 - 30 - 20
    assert stock["Pasta"] == 50


def test_stock_timeline_is_cumulative():
    timeline = stock_timeline(sample(), product="Rice")
    assert timeline["stock"].tolist() == [100, 70, 50]


def test_product_summary_columns_and_turnover():
    summary = product_summary(sample()).set_index("product")
    assert summary.loc["Rice", "received"] == 100
    assert summary.loc["Rice", "shipped"] == 50
    assert summary.loc["Rice", "stock"] == 50
    assert summary.loc["Rice", "turnover"] == 1.0  # 50 shipped / 50 stock


def test_stockout_alerts_flags_low_stock_only():
    alerts = stockout_alerts(sample(), {"Rice": 60, "Pasta": 10})
    products = alerts["product"].tolist()
    assert "Rice" in products       # stock 50 <= 60 -> alert
    assert "Pasta" not in products  # stock 50 > 10 -> no alert


def test_summary_kpis():
    k = summary_kpis(sample())
    assert k["products"] == 2
    assert k["movements"] == 4
    assert k["total_received"] == 150
    assert k["total_shipped"] == 50
    assert k["net_stock"] == 100


def test_invalid_movement_type_is_signed_nan_safe():
    # turnover should never divide by zero stock
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01", "2025-01-02"]),
            "product": ["X", "X"],
            "movement_type": ["in", "out"],
            "quantity": [10, 10],
        }
    )
    summary = product_summary(df).set_index("product")
    assert summary.loc["X", "stock"] == 0
    assert summary.loc["X", "turnover"] == 0.0
