"""Validación del CSV, cálculo de KPIs y agregación de estadísticas para Gemini.

Regla de calidad de datos (documentada en README):
- Celdas vacías en order_id, date, quantity, amount o is_purchase: la fila se
  descarta y se informa en df.attrs["quality"].
- Celdas vacías en category: se reemplazan por "Sin categoría".
- Valores presentes pero inválidos (amount="abc", fecha inexistente, order_id
  duplicado, cantidad negativa...): se rechaza el archivo con un mensaje claro.
- Tras descartar filas deben quedar al menos MIN_ROWS filas válidas.
"""
from typing import Dict, IO, List, Union

import pandas as pd

REQUIRED_COLUMNS = ["order_id", "date", "category", "quantity", "amount", "is_purchase"]
DROP_IF_MISSING = ["order_id", "date", "quantity", "amount", "is_purchase"]
MIN_ROWS = 100
MISSING_CATEGORY = "Sin categoría"
MAX_EXAMPLES = 3

_TRUE = {"1", "1.0", "true", "yes", "y", "si", "sí", "t"}
_FALSE = {"0", "0.0", "false", "no", "n", "f"}

# Única fuente de verdad de los KPIs: la usan la interfaz, README y el prompt.
KPI_DEFINITIONS = {
    "total_sales": {
        "label": "Ventas totales",
        "formula": "Σ amount de las filas con is_purchase = True",
        "description": "Ingresos generados por las transacciones que terminaron en compra.",
        "kind": "money",
    },
    "total_transactions": {
        "label": "Transacciones",
        "formula": "Número de filas válidas",
        "description": "Pedidos registrados, se hayan comprado o no.",
        "kind": "int",
    },
    "purchases_count": {
        "label": "Compras",
        "formula": "Número de filas con is_purchase = True",
        "description": "Transacciones que se concretaron como venta.",
        "kind": "int",
    },
    "conversion_rate": {
        "label": "Tasa de conversión",
        "formula": "purchases_count / total_transactions",
        "description": "Porcentaje de transacciones que terminan en compra.",
        "kind": "percent",
    },
    "avg_amount_per_purchase": {
        "label": "Ticket medio",
        "formula": "total_sales / purchases_count",
        "description": "Ingreso promedio por cada compra realizada.",
        "kind": "money",
    },
    "units_sold": {
        "label": "Unidades vendidas",
        "formula": "Σ quantity de las filas con is_purchase = True",
        "description": "Productos entregados en las compras.",
        "kind": "int",
    },
    "avg_units_per_purchase": {
        "label": "Unidades por compra",
        "formula": "units_sold / purchases_count",
        "description": "Tamaño promedio de cada compra en unidades.",
        "kind": "decimal",
    },
    "avg_unit_price": {
        "label": "Precio medio por unidad",
        "formula": "total_sales / units_sold",
        "description": "Ingreso promedio obtenido por cada unidad vendida.",
        "kind": "money",
    },
}


def format_kpi(name: str, value: float) -> str:
    kind = KPI_DEFINITIONS[name]["kind"]
    if kind == "percent":
        return f"{value * 100:.1f}%"
    if kind == "int":
        return f"{int(value):,}"
    return f"{value:,.2f}"


def _examples(series: pd.Series, mask: pd.Series) -> str:
    """'N fila(s); p. ej. línea 5: 'abc'' (línea 1 = encabezado)."""
    bad = series[mask]
    shown = "; ".join(f"línea {i + 2}: '{v}'" for i, v in bad.head(MAX_EXAMPLES).items())
    return f"{len(bad)} fila(s); p. ej. {shown}"


def to_bool_series(series: pd.Series) -> pd.Series:
    """Convierte 0/1, True/False, yes/no, sí/no a booleanos; NaN se conserva."""
    normalized = series.map(lambda v: v if pd.isna(v) else str(v).strip().lower())
    result = normalized.map(lambda v: True if v in _TRUE else False if v in _FALSE else None)
    invalid = normalized.notna() & result.isna()
    if invalid.any():
        raise ValueError(f"is_purchase inválido (usa 1/0, true/false o sí/no): {_examples(series, invalid)}.")
    return result


def _read(source: Union[str, IO]) -> pd.DataFrame:
    try:
        # Todo como texto: una celda vacía no convierte 1 en "1.0". utf-8-sig tolera el BOM de Excel.
        return pd.read_csv(source, dtype=str, encoding="utf-8-sig")
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError, OSError) as exc:
        raise ValueError("No se pudo leer el archivo. Verifica que sea un CSV válido guardado en UTF-8.") from exc


def validate_csv(source: Union[str, IO]) -> pd.DataFrame:
    """Lee y valida el CSV; devuelve un DataFrame con tipos normalizados.

    df.attrs["quality"] = {"rows_read", "rows_valid", "dropped_rows", "missing": {columna: n}}.
    """
    df = _read(source)
    df.columns = [str(c).strip().lower() for c in df.columns]
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Faltan columnas obligatorias: {', '.join(missing_cols)}. "
            f"Columnas encontradas: {', '.join(df.columns) or 'ninguna'}. "
            "Revisa el formato del CSV (separador por comas)."
        )
    if len(df) < MIN_ROWS:
        raise ValueError(f"El archivo debe tener al menos {MIN_ROWS} filas; encontrado {len(df)}.")

    df = df[REQUIRED_COLUMNS].apply(lambda s: s.str.strip())
    df = df.mask(df == "")
    missing = {c: int(n) for c, n in df.isna().sum().items() if n}

    ids = df["order_id"]
    duplicated = ids.notna() & ids.duplicated(keep=False)
    if duplicated.any():
        raise ValueError(f"order_id duplicado: {_examples(ids, duplicated)}. Cada pedido debe tener un identificador único.")

    for column in ("quantity", "amount"):
        numeric = pd.to_numeric(df[column], errors="coerce")
        if (df[column].notna() & numeric.isna()).any():
            raise ValueError(f"{column} no numérico: {_examples(df[column], df[column].notna() & numeric.isna())}.")
        df[column] = numeric.astype(float)
    bad_quantity = df["quantity"].notna() & ((df["quantity"] < 1) | (df["quantity"] % 1 != 0))
    if bad_quantity.any():
        raise ValueError(f"quantity debe ser un entero mayor o igual a 1: {_examples(df['quantity'], bad_quantity)}.")
    if (df["amount"] < 0).any():
        raise ValueError(f"amount no puede ser negativo: {_examples(df['amount'], df['amount'] < 0)}.")

    dates = pd.to_datetime(df["date"], format="ISO8601", errors="coerce")
    if (df["date"].notna() & dates.isna()).any():
        raise ValueError(f"date inválida (usa AAAA-MM-DD): {_examples(df['date'], df['date'].notna() & dates.isna())}.")
    df["date"] = dates

    df["is_purchase"] = to_bool_series(df["is_purchase"])
    df["category"] = df["category"].fillna(MISSING_CATEGORY)

    rows_read = len(df)
    df = df.dropna(subset=DROP_IF_MISSING).reset_index(drop=True)
    dropped = rows_read - len(df)
    if len(df) < MIN_ROWS:
        raise ValueError(
            f"Tras descartar {dropped} fila(s) con valores faltantes quedan {len(df)} filas válidas; "
            f"se requieren al menos {MIN_ROWS}."
        )
    df["quantity"] = df["quantity"].astype(int)
    df["is_purchase"] = df["is_purchase"].astype(bool)
    df.attrs["quality"] = {"rows_read": rows_read, "rows_valid": len(df), "dropped_rows": dropped, "missing": missing}
    return df


def _ratio(numerator: float, denominator: float, digits: int = 2) -> float:
    return round(numerator / denominator, digits) if denominator else 0.0


def compute_kpis(df: pd.DataFrame) -> Dict[str, float]:
    purchases = df[df["is_purchase"]]
    total_transactions = int(len(df))
    purchases_count = int(len(purchases))
    total_sales = round(float(purchases["amount"].sum()), 2)
    units_sold = int(purchases["quantity"].sum())
    return {
        "total_sales": total_sales,
        "total_transactions": total_transactions,
        "purchases_count": purchases_count,
        "conversion_rate": _ratio(purchases_count, total_transactions, 4),
        "avg_amount_per_purchase": _ratio(total_sales, purchases_count),
        "units_sold": units_sold,
        "avg_units_per_purchase": _ratio(units_sold, purchases_count),
        "avg_unit_price": _ratio(total_sales, units_sold),
    }


def category_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Métrica categórica: ventas, compras, unidades y participación por categoría (orden descendente)."""
    purchases = df[df["is_purchase"]]
    table = (
        purchases.groupby("category")
        .agg(sales=("amount", "sum"), purchases=("amount", "count"), units=("quantity", "sum"))
        .reindex(sorted(df["category"].unique()), fill_value=0)
        .sort_values("sales", ascending=False)
    )
    total = table["sales"].sum()
    table["share"] = (table["sales"] / total).round(4) if total else 0.0
    table["sales"] = table["sales"].round(2)
    return table


def monthly_sales(df: pd.DataFrame) -> pd.Series:
    """Ventas (solo compras) por mes calendario, incluidos meses sin compras."""
    purchases = df[df["is_purchase"]]
    months = pd.period_range(df["date"].min(), df["date"].max(), freq="M")
    return purchases.groupby(purchases["date"].dt.to_period("M"))["amount"].sum().reindex(months, fill_value=0.0).round(2)


def aggregate_for_gemini(df: pd.DataFrame) -> str:
    """Texto con estadísticas agregadas (nunca filas individuales) para el prompt."""
    kpis = compute_kpis(df)
    start, end = df["date"].min(), df["date"].max()
    quality = df.attrs.get("quality", {})
    lines: List[str] = [
        f"Periodo: {start:%Y-%m-%d} a {end:%Y-%m-%d} ({(end - start).days + 1} días)",
        f"Filas analizadas: {len(df)} (descartadas por valores faltantes: {quality.get('dropped_rows', 0)})",
    ]
    lines += [f"{d['label']}: {format_kpi(name, kpis[name])}" for name, d in KPI_DEFINITIONS.items()]
    categories = category_breakdown(df)
    lines.append("Ventas por categoría: " + "; ".join(
        f"{cat} {row.sales:,.2f} ({row.share * 100:.1f}%, {int(row.units)} unidades)" for cat, row in categories.iterrows()
    ))
    lines.append("Ventas por mes: " + "; ".join(f"{month} {value:,.2f}" for month, value in monthly_sales(df).items()))
    return "\n".join(lines)
