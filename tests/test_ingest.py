import pandas as pd

from src.ingest import REQUIRED, apply_mapping, coerce, guess_column


def test_guess_column_matches_french_headers():
    cols = ["Date_mouvement", "Article", "Quantité", "Sens"]
    assert guess_column(cols, "date") == "Date_mouvement"
    assert guess_column(cols, "product") == "Article"
    assert guess_column(cols, "quantity") == "Quantité"
    assert guess_column(cols, "movement_type") == "Sens"


def test_apply_mapping_normalizes_foreign_csv():
    raw = pd.DataFrame(
        {
            "Date_mouvement": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "Article": ["Riz", "Riz", "Pates"],
            "Quantité": [100, 30, 50],
            "Sens": ["Entrée", "Sortie", "Entrée"],
        }
    )
    df = apply_mapping(
        raw, "Date_mouvement", "Article", "Quantité", "Sens", in_values={"Entrée"}
    )
    assert list(df.columns) == REQUIRED
    assert df["movement_type"].tolist() == ["in", "out", "in"]
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert df["quantity"].tolist() == [100, 30, 50]


def test_coerce_filters_invalid_rows():
    raw = pd.DataFrame(
        {
            "date": ["2025-01-01", "not-a-date", "2025-01-03"],
            "product": ["A", "B", "C"],
            "movement_type": ["IN", "out", "weird"],
            "quantity": [10, 5, 7],
        }
    )
    df = coerce(raw)
    # row 2 dropped (bad date), row 3 dropped (bad movement_type)
    assert len(df) == 1
    assert df.iloc[0]["movement_type"] == "in"
