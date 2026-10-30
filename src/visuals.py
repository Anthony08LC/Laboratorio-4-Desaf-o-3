"""Visualizaciones: serie temporal de ventas y distribución por categoría.

Regla de faltantes: los días sin compras se muestran con ventas = 0.
"""
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.kpis import category_breakdown  # noqa: E402

COLOR = "#1f5fa8"


def sales_timeseries(df: pd.DataFrame) -> pd.Series:
    purchases = df[df["is_purchase"]]
    daily = purchases.groupby(purchases["date"].dt.normalize())["amount"].sum()
    full_range = pd.date_range(df["date"].min().normalize(), df["date"].max().normalize(), freq="D")
    return daily.reindex(full_range, fill_value=0.0)


def timeseries_figure(df: pd.DataFrame):
    series = sales_timeseries(df)
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.plot(series.index, series.values, color=COLOR, linewidth=1.5)
    ax.set_title("Ventas diarias (solo compras)")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Ventas")
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


def category_figure(df: pd.DataFrame):
    table = category_breakdown(df)
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.bar(table.index.astype(str), table["sales"], color=COLOR)
    ax.set_title("Ventas por categoría")
    ax.set_ylabel("Ventas")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig


def fig_to_png(fig) -> bytes:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=120)
    plt.close(fig)
    return buffer.getvalue()
