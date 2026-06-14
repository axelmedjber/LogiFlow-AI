"""Train and evaluate the stockout-risk classifier.

A gradient-boosting classifier predicts the probability that a product will run
out of stock before its next replenishment. We report accuracy, ROC-AUC and a
classification report on a held-out test set, then save the model with joblib.

Run:

    python -m ml.train
"""

from __future__ import annotations

from pathlib import Path

import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report, roc_auc_score, accuracy_score
from sklearn.model_selection import train_test_split

from ml.dataset import make_dataset
from ml.features import FEATURES, TARGET

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "stockout_model.pkl"


def main() -> dict:
    df = make_dataset()
    X, y = df[FEATURES], df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = GradientBoostingClassifier(random_state=42)
    model.fit(X_train, y_train)

    proba = model.predict_proba(X_test)[:, 1]
    pred = model.predict(X_test)
    metrics = {
        "accuracy": accuracy_score(y_test, pred),
        "roc_auc": roc_auc_score(y_test, proba),
    }

    print(f"Test accuracy : {metrics['accuracy']:.3f}")
    print(f"Test ROC-AUC  : {metrics['roc_auc']:.3f}\n")
    print(classification_report(y_test, pred, target_names=["ok", "stockout"]))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")
    return metrics


if __name__ == "__main__":
    main()
