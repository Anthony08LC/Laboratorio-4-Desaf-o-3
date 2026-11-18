"""Visualizaciones: evolución de ventas en el tiempo y ventas por categoría.

Regla de faltantes: los periodos sin compras se muestran con ventas = 0.
"""
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from src.kpis import category_breakdown  # noqa: E402

COLOR = "#2a78d6"
TEXT = "#0b0b0b"
MUTED = "#52514e"
GRID = "#e4e3df"
SURFACE = "#fcfcfb"
DAILY_MAX_DAYS = 31  # periodos más largos se agregan por semana para reducir ruido

_thousands = FuncFormatter(lambda v, _: f"{v:,.0f}")


def sales_timeseries(df: pd.DataFrame, freq: str = "D") -> pd.Series:
    """Ventas (solo compras) por día ("D") o semana ("W-MON"), con ceros en periodos sin compras."""
    purchases = df[df["is_purchase"]]
    full_range = pd.date_range(df["date"].min().normalize(), df["date"].max().normalize(), freq="D")
    daily = purchases.groupby(purchases["date"].dt.normalize())["amount"].sum().reindex(full_range, fill_value=0.0)
    return daily if freq == "D" else daily.resample(freq, label="left", closed="left").sum()


def _style(ax, title: str):
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold", color=TEXT, pad=10)
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)


def timeseries_figure(df: pd.DataFrame):
    span_days = (df["date"].max() - df["date"].min()).days + 1
    freq, unit = ("D", "día") if span_days <= DAILY_MAX_DAYS else ("W-MON", "semana")
    series = sales_timeseries(df, freq)
    fig, ax = plt.subplots(figsize=(8, 3.8), facecolor=SURFACE)
    ax.plot(series.index, series.values, color=COLOR, linewidth=2, marker="o", markersize=5)
    xlabel = "Fecha"
    if freq != "D":
        # Semanas en los extremos del periodo con menos de 7 días de datos: marcador hueco.
        period = pd.date_range(df["date"].min().normalize(), df["date"].max().normalize(), freq="D")
        days = pd.Series(1, index=period).resample(freq, label="left", closed="left").sum()
        partial = series[days < 7]
        if not partial.empty:
            ax.plot(partial.index, partial.values, "o", markersize=7, color=SURFACE, markeredgecolor=COLOR, markeredgewidth=2)
            xlabel = "Semana (inicia en lunes) · ○ semana incompleta del periodo"
        else:
            xlabel = "Semana (inicia en lunes)"
    peak = series.idxmax()
    ax.annotate(f"Máximo: {series[peak]:,.0f}", (peak, series[peak]), textcoords="offset points",
                xytext=(0, 8), ha="center", fontsize=9, color=TEXT)
    _style(ax, f"Evolución de ventas por {unit}")
    ax.set_xlabel(xlabel, color=MUTED, fontsize=9)
    ax.set_ylabel("Ventas (monto)", color=MUTED, fontsize=9)
    ax.yaxis.set_major_formatter(_thousands)
    ax.set_ylim(0, series.max() * 1.18 or 1)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


def category_figure(df: pd.DataFrame):
    table = category_breakdown(df).iloc[::-1]  # la mayor arriba
    fig, ax = plt.subplots(figsize=(8, 3.8), facecolor=SURFACE)
    bars = ax.barh(table.index.astype(str), table["sales"], color=COLOR, height=0.6)
    ax.bar_label(bars, labels=[f"{s:,.0f}  ({p * 100:.1f}%)" for s, p in zip(table["sales"], table["share"])],
                 padding=4, fontsize=9, color=TEXT)
    _style(ax, "Ventas por categoría (participación sobre el total)")
    ax.set_xlabel("Ventas (monto)", color=MUTED, fontsize=9)
    ax.xaxis.set_major_formatter(_thousands)
    ax.set_xlim(0, table["sales"].max() * 1.3 or 1)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return fig


def fig_to_png(fig) -> bytes:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)
    return buffer.getvalue()
