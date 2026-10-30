import csv

import pandas as pd
import pytest

from src.kpis import aggregate_for_gemini, category_breakdown, compute_kpis, to_bool_series, validate_csv
from tests.conftest import make_rows, write_csv


def test_validate_csv_and_compute_kpis(sample_csv):
    df = validate_csv(str(sample_csv))
    with sample_csv.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    expected_sales = round(sum(float(r["amount"]) for r in rows if r["is_purchase"] == "1"), 2)
    expected_purchases = sum(r["is_purchase"] == "1" for r in rows)

    kpis = compute_kpis(df)

    assert kpis["total_transactions"] == len(rows)
    assert kpis["purchases_count"] == expected_purchases
    assert kpis["total_sales"] == pytest.approx(expected_sales, abs=0.01)
    assert kpis["avg_amount_per_purchase"] == pytest.approx(expected_sales / expected_purchases, abs=0.01)
    assert kpis["conversion_rate"] == pytest.approx(expected_purchases / len(rows), abs=1e-4)
    assert kpis["ticket_mean"] == pytest.approx(expected_sales / len(rows), abs=0.01)


def test_validate_csv_normalizes_types(sample_csv):
    df = validate_csv(str(sample_csv))
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert df["amount"].dtype == float
    assert df["is_purchase"].dtype == bool


def test_missing_columns(tmp_path):
    path = write_csv(tmp_path / "x.csv", ["1,2026-01-01,10"] * 120, header="order_id,date,amount")
    with pytest.raises(ValueError, match="Faltan columnas obligatorias: category, is_purchase"):
        validate_csv(str(path))


def test_less_than_100_rows(tmp_path):
    path = write_csv(tmp_path / "x.csv", make_rows(99))
    with pytest.raises(ValueError, match="al menos 100 filas; encontrado 99"):
        validate_csv(str(path))


def test_amount_not_numeric(tmp_path):
    path = write_csv(tmp_path / "x.csv", make_rows(100) + ["X,2026-01-01,A,abc,1"])
    with pytest.raises(ValueError, match="amount no numérico"):
        validate_csv(str(path))


def test_is_purchase_invalid(tmp_path):
    path = write_csv(tmp_path / "x.csv", make_rows(100) + ["X,2026-01-01,A,5,quizas"])
    with pytest.raises(ValueError, match="is_purchase inválido"):
        validate_csv(str(path))


def test_invalid_date(tmp_path):
    path = write_csv(tmp_path / "x.csv", make_rows(100) + ["X,no-es-fecha,A,5,1"])
    with pytest.raises(ValueError, match="date inválida"):
        validate_csv(str(path))


def test_unreadable_file(tmp_path):
    path = tmp_path / "bin.csv"
    path.write_bytes(b"\xff\xfe\x00\x00\x81\x82")
    with pytest.raises(ValueError, match="No se pudo leer el archivo"):
        validate_csv(str(path))


def test_empty_file(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="No se pudo leer el archivo"):
        validate_csv(str(path))


def test_mixed_boolean_formats():
    series = pd.Series(["1", "0", "True", "false", "yes", "No", "sí", 1, 0, None])
    result = to_bool_series(series)
    assert result.tolist()[:9] == [True, False, True, False, True, False, True, True, False]
    assert pd.isna(result.iloc[9])


def test_missing_values_rule(tmp_path):
    rows = make_rows(100) + ["M1,,A,5,1", "M2,2026-01-01,A,,1", "M3,2026-01-01,A,5,", "M4,2026-01-01,,7,1"]
    df = validate_csv(str(write_csv(tmp_path / "x.csv", rows)))
    assert len(df) == 101
    assert df.attrs["dropped_rows"] == 3
    assert "Sin categoría" in set(df["category"])


def test_accepts_file_like_buffer(sample_csv):
    with sample_csv.open("rb") as f:
        df = validate_csv(f)
    assert len(df) == 200


def test_compute_kpis_without_purchases(tmp_path):
    df = validate_csv(str(write_csv(tmp_path / "x.csv", make_rows(100, is_purchase="0"))))
    kpis = compute_kpis(df)
    assert kpis["total_sales"] == 0.0
    assert kpis["purchases_count"] == 0
    assert kpis["avg_amount_per_purchase"] == 0.0
    assert kpis["conversion_rate"] == 0.0
    assert kpis["avg_amount_per_transaction"] == 10.0


def test_total_sales_only_counts_purchases(tmp_path):
    rows = make_rows(50, amount="10.005", is_purchase="1") + make_rows(50, amount="999", is_purchase="0")
    kpis = compute_kpis(validate_csv(str(write_csv(tmp_path / "x.csv", rows))))
    assert kpis["total_sales"] == 500.25
    assert kpis["conversion_rate"] == 0.5


def test_category_breakdown(sample_csv):
    df = validate_csv(str(sample_csv))
    table = category_breakdown(df)
    assert table["sales"].is_monotonic_decreasing
    assert table["sales"].sum() == pytest.approx(compute_kpis(df)["total_sales"], abs=0.05)


def test_aggregate_for_gemini_is_short_and_has_no_rows(sample_csv):
    df = validate_csv(str(sample_csv))
    text = aggregate_for_gemini(compute_kpis(df), category_breakdown(df))
    assert len(text) <= 500
    assert "Ventas totales" in text and "Tasa de conversión" in text and "Top categorías" in text
    assert "ORD-" not in text
