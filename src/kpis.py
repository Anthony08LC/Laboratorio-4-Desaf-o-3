"""Validación del CSV, cálculo de KPIs y agregación de estadísticas para Gemini.

Regla de valores faltantes (documentada en README):
- Celdas vacías en date, amount o is_purchase: la fila se descarta y se cuenta
  en df.attrs["dropped_rows"].
- Celdas vacías en category: se reemplazan por "Sin categoría".
- Valores presentes pero inválidos (p. ej. amount="abc"): se rechaza el archivo.
"""
from typing import Dict, IO, Union

import pandas as pd

REQUIRED_COLUMNS = ["order_id", "date", "category", "amount", "is_purchase"]
MIN_ROWS = 100
MISSING_CATEGORY = "Sin categoría"

_TRUE = {"1", "1.0", "true", "yes", "y", "si", "sí", "t"}
_FALSE = {"0", "0.0", "false", "no", "n", "f"}

KPI_FORMULAS = {
    "total_sales": "Σ amount de las filas con is_purchase = True",
    "total_transactions": "Número de filas válidas",
    "purchases_count": "Número de filas con is_purchase = True",
    "avg_amount_per_transaction": "Σ amount (todas las filas) / total_transactions",
    "avg_amount_per_purchase": "total_sales / purchases_count",
    "conversion_rate": "purchases_count / total_transactions",
    "ticket_mean": "total_sales / total_transactions (ingreso medio por transacción)",
}


def to_bool_series(series: pd.Series) -> pd.Series:
    """Convierte 0/1, True/False, yes/no, sí/no a booleanos; NaN se conserva."""
    normalized = series.map(lambda v: v if pd.isna(v) else str(v).strip().lower())
    result = normalized.map(lambda v: True if v in _TRUE else False if v in _FALSE else None)
    invalid = normalized.notna() & result.isna()
    if invalid.any():
        examples = ", ".join(sorted({str(v) for v in series[invalid]})[:3])
        raise ValueError(f"is_purchase inválido: valores no reconocidos ({examples}).")
    return result


def validate_csv(source: Union[str, IO]) -> pd.DataFrame:
    """Lee y valida el CSV; devuelve un DataFrame con tipos normalizados."""
    try:
        # Se lee todo como texto para que una celda vacía no convierta 1 en "1.0".
        df = pd.read_csv(source, dtype=str)
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError, OSError) as exc:
        raise ValueError("No se pudo leer el archivo. Verifica que sea un CSV válido.") from exc

    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Faltan columnas obligatorias: {', '.join(missing)}. Revisa el formato del CSV."
        )
    if len(df) < MIN_ROWS:
        raise ValueError(f"El archivo debe tener al menos {MIN_ROWS} filas; encontrado {len(df)}.")

    df = df[REQUIRED_COLUMNS].copy()

    amount = pd.to_numeric(df["amount"], errors="coerce")
    if (df["amount"].notna() & amount.isna()).any():
        raise ValueError("amount no numérico: revisa la columna amount.")
    df["amount"] = amount.astype(float)

    dates = pd.to_datetime(df["date"], errors="coerce")
    if (df["date"].notna() & dates.isna()).any():
        raise ValueError("date inválida: usa el formato AAAA-MM-DD.")
    df["date"] = dates

    df["is_purchase"] = to_bool_series(df["is_purchase"])

    df["category"] = df["category"].fillna(MISSING_CATEGORY).astype(str).str.strip()

    before = len(df)
    df = df.dropna(subset=["date", "amount", "is_purchase"]).reset_index(drop=True)
    df["is_purchase"] = df["is_purchase"].astype(bool)
    df.attrs["dropped_rows"] = before - len(df)
    if df.empty:
        raise ValueError("El archivo no contiene filas válidas tras eliminar valores faltantes.")
    return df


def compute_kpis(df: pd.DataFrame) -> Dict[str, float]:
    total_transactions = int(len(df))
    purchases = df[df["is_purchase"]]
    purchases_count = int(len(purchases))
    total_sales = round(float(purchases["amount"].sum()), 2)
    return {
        "total_sales": total_sales,
        "total_transactions": total_transactions,
        "purchases_count": purchases_count,
        "avg_amount_per_transaction": round(float(df["amount"].mean()), 2) if total_transactions else 0.0,
        "avg_amount_per_purchase": round(total_sales / purchases_count, 2) if purchases_count else 0.0,
        "conversion_rate": round(purchases_count / total_transactions, 4) if total_transactions else 0.0,
        "ticket_mean": round(total_sales / total_transactions, 2) if total_transactions else 0.0,
    }


def category_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Métrica categórica: ventas y número de compras por categoría (orden descendente)."""
    purchases = df[df["is_purchase"]]
    table = (
        purchases.groupby("category")["amount"]
        .agg(sales="sum", purchases="count")
        .reindex(sorted(df["category"].unique()), fill_value=0)
        .sort_values("sales", ascending=False)
    )
    table["sales"] = table["sales"].round(2)
    return table


def aggregate_for_gemini(kpis: Dict[str, float], categories: pd.DataFrame = None) -> str:
    """Texto con estadísticas agregadas (sin filas individuales) para el prompt."""
    lines = [
        f"Ventas totales: {kpis['total_sales']:.2f}",
        f"Transacciones: {kpis['total_transactions']}",
        f"Compras: {kpis['purchases_count']}",
        f"Tasa de conversión: {kpis['conversion_rate'] * 100:.1f}%",
        f"Monto medio por compra: {kpis['avg_amount_per_purchase']:.2f}",
        f"Monto medio por transacción: {kpis['avg_amount_per_transaction']:.2f}",
        f"Ingreso medio por transacción: {kpis['ticket_mean']:.2f}",
    ]
    if categories is not None and not categories.empty:
        top = ", ".join(f"{cat} {row.sales:.2f}" for cat, row in categories.head(3).iterrows())
        lines.append(f"Top categorías por ventas: {top}")
    return "\n".join(lines)
