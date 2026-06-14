"""Tests for the stockout-risk ML module.

Skipped automatically when scikit-learn is not installed.
"""

import pandas as pd
import pytest

pytest.importorskip("sklearn")

from ml.dataset import make_dataset  # noqa: E402
from ml.features import FEATURES, TARGET, product_features  # noqa: E402
from ml.train import MODEL_PATH  # noqa: E402


def test_dataset_has_features_and_label():
    df = make_dataset(n=200)
    for col in FEATURES + [TARGET]:
        assert col in df.columns
    assert set(df[TARGET].unique()) <= {0, 1}
    assert len(df) == 200


def test_product_features_schema():
    movements = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03"]),
            "product": ["Rice", "Rice", "Pasta"],
            "movement_type": ["in", "out", "in"],
            "quantity": [100, 20, 50],
        }
    )
    feats = product_features(movements, lead_time_days=5)
    assert list(feats.columns) == FEATURES
    assert feats.loc["Rice", "current_stock"] == 80  # 100 in - 20 out
    assert feats.loc["Pasta", "current_stock"] == 50


def test_model_scores_products_if_present():
    if not MODEL_PATH.exists():
        pytest.skip("trained model not present (run `python -m ml.train`)")
    import joblib

    movements = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01", "2025-01-02"]),
            "product": ["Rice", "Rice"],
            "movement_type": ["in", "out"],
            "quantity": [100, 10],
        }
    )
    model = joblib.load(MODEL_PATH)
    proba = model.predict_proba(product_features(movements))[:, 1]
    assert ((proba >= 0) & (proba <= 1)).all()
