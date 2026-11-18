import pandas as pd
import pytest

from src.kpis import compute_kpis, validate_csv
from src.visuals import category_figure, fig_to_png, sales_timeseries, timeseries_figure

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def frame(dates, amounts, purchases=None):
    return pd.DataFrame({
        "date": pd.to_datetime(dates),
        "category": ["A"] * len(dates),
        "quantity": [1] * len(dates),
        "amount": amounts,
        "is_purchase": purchases or [True] * len(dates),
    })


def test_figures_export_png(sample_csv):
    df = validate_csv(str(sample_csv))
    for builder in (timeseries_figure, category_figure):
        png = fig_to_png(builder(df))
        assert png.startswith(PNG_SIGNATURE)
        assert len(png) > 1000


def test_timeseries_figure_has_title_and_labels(sample_csv):
    fig = timeseries_figure(validate_csv(str(sample_csv)))
    ax = fig.axes[0]
    assert ax.get_title(loc="left") == "Evolución de ventas por semana"  # 89 días → agregación semanal
    assert ax.get_ylabel() == "Ventas (monto)"
    assert "semana incompleta" in ax.get_xlabel()
    fig_to_png(fig)


def test_category_figure_shows_values_and_share(sample_csv):
    df = validate_csv(str(sample_csv))
    fig = category_figure(df)
    ax = fig.axes[0]
    labels = [t.get_text() for t in ax.texts]
    assert ax.get_title(loc="left").startswith("Ventas por categoría")
    assert len(labels) == df["category"].nunique()
    assert all("%" in label for label in labels)
    fig_to_png(fig)


def test_short_period_uses_daily_chart():
    fig = timeseries_figure(frame(["2026-01-01", "2026-01-10"], [10.0, 5.0]))
    assert fig.axes[0].get_title(loc="left") == "Evolución de ventas por día"
    fig_to_png(fig)


def test_timeseries_fills_missing_days_with_zero():
    series = sales_timeseries(frame(["2026-01-01", "2026-01-04"], [10.0, 5.0]))
    assert series.tolist() == [10.0, 0.0, 0.0, 5.0]


def test_timeseries_ignores_non_purchases():
    series = sales_timeseries(frame(["2026-01-01", "2026-01-02"], [10.0, 99.0], purchases=[True, False]))
    assert series.tolist() == [10.0, 0.0]


def test_weekly_series_preserves_total(sample_csv):
    df = validate_csv(str(sample_csv))
    weekly = sales_timeseries(df, "W-MON")
    assert all(day.weekday() == 0 for day in weekly.index)
    assert weekly.sum() == pytest.approx(compute_kpis(df)["total_sales"], abs=0.01)
