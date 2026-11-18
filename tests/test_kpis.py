import csv

import pandas as pd
import pytest

from src.kpis import (
    KPI_DEFINITIONS,
    aggregate_for_gemini,
    category_breakdown,
    compute_kpis,
    format_kpi,
    monthly_sales,
    to_bool_series,
    validate_csv,
)
from tests.conftest import make_rows, write_csv


def csv_with(tmp_path, extra_rows, **kwargs):
    return str(write_csv(tmp_path / "x.csv", make_rows(100, **kwargs) + extra_rows))


# --- Carga y validación -------------------------------------------------------------

def test_validate_csv_and_compute_kpis(sample_csv):
    df = validate_csv(str(sample_csv))
    with sample_csv.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    purchases = [r for r in rows if r["is_purchase"] == "1"]
    expected_sales = sum(float(r["amount"]) for r in purchases)
    expected_units = sum(int(r["quantity"]) for r in purchases)

    kpis = compute_kpis(df)

    assert kpis["total_transactions"] == len(rows)
    assert kpis["purchases_count"] == len(purchases)
    assert kpis["total_sales"] == pytest.approx(expected_sales, abs=0.01)
    assert kpis["conversion_rate"] == pytest.approx(len(purchases) / len(rows), abs=1e-4)
    assert kpis["avg_amount_per_purchase"] == pytest.approx(expected_sales / len(purchases), abs=0.01)
    assert kpis["units_sold"] == expected_units
    assert kpis["avg_units_per_purchase"] == pytest.approx(expected_units / len(purchases), abs=0.01)
    assert kpis["avg_unit_price"] == pytest.approx(expected_sales / expected_units, abs=0.01)


def test_validate_csv_normalizes_types(sample_csv):
    df = validate_csv(str(sample_csv))
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert df["amount"].dtype == float
    assert pd.api.types.is_integer_dtype(df["quantity"])
    assert df["is_purchase"].dtype == bool
    assert df.attrs["quality"] == {"rows_read": 200, "rows_valid": 200, "dropped_rows": 0, "missing": {}}


def test_accepts_file_like_buffer(sample_csv):
    with sample_csv.open("rb") as f:
        assert len(validate_csv(f)) == 200


def test_accepts_utf8_bom_and_extra_columns(tmp_path):
    path = tmp_path / "excel.csv"
    rows = [r + ",extra" for r in make_rows(100)]
    path.write_text("﻿" + "\n".join(["Order_ID, Date ,category,quantity,amount,is_purchase,notas", *rows]), encoding="utf-8")
    df = validate_csv(str(path))
    assert list(df.columns) == ["order_id", "date", "category", "quantity", "amount", "is_purchase"]


def test_empty_file(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="No se pudo leer el archivo"):
        validate_csv(str(path))


def test_header_only(tmp_path):
    with pytest.raises(ValueError, match="al menos 100 filas; encontrado 0"):
        validate_csv(str(write_csv(tmp_path / "x.csv", [])))


def test_unreadable_file(tmp_path):
    path = tmp_path / "bin.csv"
    path.write_bytes(b"\xff\xfe\x00\x00\x81\x82")
    with pytest.raises(ValueError, match="No se pudo leer el archivo"):
        validate_csv(str(path))


def test_missing_columns(tmp_path):
    path = write_csv(tmp_path / "x.csv", ["1,2026-01-01,10"] * 120, header="order_id,date,amount")
    with pytest.raises(ValueError, match="Faltan columnas obligatorias: category, quantity, is_purchase"):
        validate_csv(str(path))


def test_wrong_delimiter_reports_found_columns(tmp_path):
    rows = [r.replace(",", ";") for r in make_rows(100)]
    path = write_csv(tmp_path / "x.csv", rows, header="order_id;date;category;quantity;amount;is_purchase")
    with pytest.raises(ValueError, match="Columnas encontradas: order_id;date"):
        validate_csv(str(path))


def test_less_than_100_rows(tmp_path):
    with pytest.raises(ValueError, match="al menos 100 filas; encontrado 99"):
        validate_csv(str(write_csv(tmp_path / "x.csv", make_rows(99))))


@pytest.mark.parametrize("row, message", [
    ("X,2026-01-01,A,1,abc,1", "amount no numérico: 1 fila\\(s\\); p. ej. línea 102: 'abc'"),
    ("X,2026-01-01,A,1,-5,1", "amount no puede ser negativo"),
    ("X,2026-01-01,A,dos,5,1", "quantity no numérico"),
    ("X,2026-01-01,A,0,5,1", "quantity debe ser un entero mayor o igual a 1"),
    ("X,2026-01-01,A,1.5,5,1", "quantity debe ser un entero mayor o igual a 1"),
    ("X,2026-01-01,A,1,5,quizas", "is_purchase inválido"),
    ("X,no-es-fecha,A,1,5,1", "date inválida"),
    ("X,2026-02-30,A,1,5,1", "date inválida"),
])
def test_invalid_types_are_rejected(tmp_path, row, message):
    with pytest.raises(ValueError, match=message):
        validate_csv(csv_with(tmp_path, [row]))


def test_duplicated_order_id(tmp_path):
    with pytest.raises(ValueError, match="order_id duplicado: 2 fila\\(s\\); p. ej. línea 2: 'O0'"):
        validate_csv(csv_with(tmp_path, ["O0,2026-01-05,A,1,5,1"]))


def test_mixed_boolean_formats():
    series = pd.Series(["1", "0", "True", "false", "yes", "No", "sí", 1, 0, None])
    result = to_bool_series(series)
    assert result.tolist()[:9] == [True, False, True, False, True, False, True, True, False]
    assert pd.isna(result.iloc[9])


def test_missing_values_are_dropped_and_reported(tmp_path):
    extra = [
        ",2026-01-01,A,1,5,1",       # order_id vacío
        "M1,,A,1,5,1",               # date vacía
        "M2,2026-01-01,A,,5,1",      # quantity vacía
        "M3,2026-01-01,A,1,,1",      # amount vacío
        "M4,2026-01-01,A,1,5,",      # is_purchase vacío
        "M5,2026-01-01,  ,1,7,1",    # category vacía (solo espacios)
    ]
    df = validate_csv(csv_with(tmp_path, extra))
    quality = df.attrs["quality"]
    assert len(df) == 101
    assert quality["rows_read"] == 106 and quality["dropped_rows"] == 5
    assert quality["missing"] == {"order_id": 1, "date": 1, "category": 1, "quantity": 1, "amount": 1, "is_purchase": 1}
    assert "Sin categoría" in set(df["category"])


def test_too_few_valid_rows_after_dropping(tmp_path):
    rows = make_rows(98) + ["M1,,A,1,5,1", "M2,,A,1,5,1", "M3,,A,1,5,1"]
    with pytest.raises(ValueError, match="Tras descartar 3 fila\\(s\\) con valores faltantes quedan 98 filas válidas"):
        validate_csv(str(write_csv(tmp_path / "x.csv", rows)))


# --- KPI ------------------------------------------------------------------------------

def test_kpis_without_purchases_avoid_division_by_zero(tmp_path):
    kpis = compute_kpis(validate_csv(csv_with(tmp_path, [], is_purchase="0")))
    assert kpis == {
        "total_sales": 0.0, "total_transactions": 100, "purchases_count": 0, "conversion_rate": 0.0,
        "avg_amount_per_purchase": 0.0, "units_sold": 0, "avg_units_per_purchase": 0.0, "avg_unit_price": 0.0,
    }


def test_kpis_known_values(tmp_path):
    rows = make_rows(50, amount="10.5", quantity="3") + make_rows(50, amount="999", quantity="9", is_purchase="0", prefix="N")
    kpis = compute_kpis(validate_csv(str(write_csv(tmp_path / "x.csv", rows))))
    assert kpis["total_sales"] == 525.0  # las 50 filas sin compra no suman
    assert kpis["conversion_rate"] == 0.5
    assert kpis["avg_amount_per_purchase"] == 10.5
    assert kpis["units_sold"] == 150
    assert kpis["avg_units_per_purchase"] == 3.0
    assert kpis["avg_unit_price"] == 3.5


def test_every_kpi_has_definition():
    df_kpis = compute_kpis(pd.DataFrame({"is_purchase": [True], "amount": [10.0], "quantity": [2]}))
    assert set(df_kpis) == set(KPI_DEFINITIONS)
    for definition in KPI_DEFINITIONS.values():
        assert definition["label"] and definition["formula"] and definition["description"]


def test_format_kpi():
    assert format_kpi("total_sales", 22677.711) == "22,677.71"
    assert format_kpi("conversion_rate", 0.595) == "59.5%"
    assert format_kpi("units_sold", 376) == "376"


def test_category_breakdown(sample_csv):
    df = validate_csv(str(sample_csv))
    table = category_breakdown(df)
    assert table["sales"].is_monotonic_decreasing
    assert table["sales"].sum() == pytest.approx(compute_kpis(df)["total_sales"], abs=0.05)
    assert table["units"].sum() == compute_kpis(df)["units_sold"]
    assert table["share"].sum() == pytest.approx(1.0, abs=0.001)


def test_monthly_sales_includes_months_without_purchases(tmp_path):
    rows = make_rows(100) + ["Z1,2026-03-10,A,1,5,0"]
    series = monthly_sales(validate_csv(str(write_csv(tmp_path / "x.csv", rows))))
    assert [str(p) for p in series.index] == ["2026-01", "2026-02", "2026-03"]
    assert series.tolist() == [1000.0, 0.0, 0.0]


def test_aggregate_for_gemini_has_only_aggregates(sample_csv):
    df = validate_csv(str(sample_csv))
    text = aggregate_for_gemini(df)
    assert len(text) <= 1000
    for label in ("Periodo", "Ventas totales", "Tasa de conversión", "Unidades vendidas", "Ventas por categoría", "Ventas por mes"):
        assert label in text
    assert "ORD-" not in text
    assert str(df.loc[0, "amount"]) not in text
