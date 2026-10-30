import pandas as pd

from src.kpis import validate_csv
from src.visuals import category_figure, fig_to_png, sales_timeseries, timeseries_figure

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def test_figures_export_png(sample_csv):
    df = validate_csv(str(sample_csv))
    for builder in (timeseries_figure, category_figure):
        png = fig_to_png(builder(df))
        assert png.startswith(PNG_SIGNATURE)
        assert len(png) > 1000


def test_timeseries_fills_missing_days_with_zero():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2026-01-01", "2026-01-04"]),
        "category": ["A", "A"],
        "amount": [10.0, 5.0],
        "is_purchase": [True, True],
    })
    series = sales_timeseries(df)
    assert len(series) == 4
    assert series.tolist() == [10.0, 0.0, 0.0, 5.0]
