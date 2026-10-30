"""Analista ejecutivo de datos con voz — interfaz Streamlit.

Ejecutar: streamlit run app.py
"""
import logging
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from data.generate_sample import OUTPUT as SAMPLE_PATH, generate as generate_sample
from src.eleven_client import synthesize_audio
from src.gemini_client import generate_summary
from src.kpis import KPI_FORMULAS, aggregate_for_gemini, category_breakdown, compute_kpis, validate_csv
from src.session import SessionHistory
from src.visuals import category_figure, fig_to_png, timeseries_figure

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

MAX_FILE_MB = 10
KPI_LABELS = {
    "total_sales": "Ventas totales",
    "total_transactions": "Transacciones",
    "purchases_count": "Compras",
    "avg_amount_per_transaction": "Monto medio por transacción",
    "avg_amount_per_purchase": "Monto medio por compra",
    "conversion_rate": "Tasa de conversión",
    "ticket_mean": "Ingreso medio por transacción",
}

st.set_page_config(page_title="Analista ejecutivo con voz", layout="wide")
st.title("Analista ejecutivo de datos con voz")

if "history" not in st.session_state:
    st.session_state.history = SessionHistory()
if "last" not in st.session_state:
    st.session_state.last = None

for key, service in (("GEMINI_API_KEY", "Gemini"), ("ELEVENLABS_API_KEY", "ElevenLabs")):
    if not os.getenv(key, "").strip():
        st.warning(f"Clave de {service} no configurada. Usando respuesta simulada marcada como SIMULADA.")

st.info("Privacidad: a Gemini solo se envían estadísticas agregadas, nunca filas individuales. No subas datos personales.")

uploaded = st.file_uploader("Sube un CSV de ventas", type=["csv"])
use_sample = st.checkbox("Usar datos de ejemplo (data/sample_sales.csv)")

source = None
if uploaded is not None:
    if uploaded.size > MAX_FILE_MB * 1024 * 1024:
        st.error(f"El archivo supera el máximo de {MAX_FILE_MB} MB.")
        st.stop()
    source = uploaded
elif use_sample:
    if not Path(SAMPLE_PATH).exists():
        generate_sample()
    source = str(SAMPLE_PATH)

if source is None:
    st.caption("Columnas obligatorias: order_id, date, category, amount, is_purchase (≥100 filas).")
    st.stop()

try:
    df = validate_csv(source)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

dropped = df.attrs.get("dropped_rows", 0)
st.success(f"CSV válido: {len(df)} filas procesadas." + (f" Se descartaron {dropped} filas con valores faltantes." if dropped else ""))

kpis = compute_kpis(df)
categories = category_breakdown(df)

st.subheader("KPIs")
cols = st.columns(4)
for i, (name, value) in enumerate(kpis.items()):
    shown = f"{value * 100:.1f}%" if name == "conversion_rate" else f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
    cols[i % 4].metric(KPI_LABELS[name], shown, help=KPI_FORMULAS[name])
with st.expander("Fórmulas de los KPIs"):
    for name, formula in KPI_FORMULAS.items():
        st.markdown(f"- **{KPI_LABELS[name]}** (`{name}`): {formula}")
st.markdown(f"**Categoría líder en ventas:** {categories.index[0]}")

st.subheader("Visualizaciones")
left, right = st.columns(2)
for column, fig_builder, label, filename in (
    (left, timeseries_figure, "Descargar serie temporal", "serie_temporal.png"),
    (right, category_figure, "Descargar ventas por categoría", "ventas_categoria.png"),
):
    png = fig_to_png(fig_builder(df))
    column.image(png)
    column.download_button(label, png, file_name=filename, mime="image/png")
st.caption("Regla de faltantes: filas sin fecha, monto o is_purchase se descartan; los días sin compras se muestran con ventas = 0.")

st.subheader("Resumen ejecutivo")
stats = aggregate_for_gemini(kpis, categories)
with st.expander("Estadísticas agregadas enviadas a Gemini"):
    st.code(stats)

if st.button("Generar resumen y audio", type="primary"):
    with st.spinner("Generando resumen..."):
        summary = generate_summary(stats)
    with st.spinner("Generando audio..."):
        audio = synthesize_audio(summary["text"])
    st.session_state.history.add(summary["text"], summary["simulated"], audio["simulated"])
    st.session_state.last = {"summary": summary, "audio": audio}

last = st.session_state.last
if last:
    summary, audio = last["summary"], last["audio"]
    for message in (summary["error"], summary["warning"], audio["error"]):
        if message:
            st.warning(message)
    if summary["simulated"]:
        st.markdown("**Resumen SIMULADA**")
    st.text(summary["text"])
    st.markdown("**Audio SIMULADA (tono de prueba)**" if audio["simulated"] else "**Audio del resumen**")
    st.audio(audio["audio"], format=audio["mime"])
    st.download_button("Exportar resumen (.txt)", summary["text"], file_name="resumen_ejecutivo.txt", mime="text/plain")

history = st.session_state.history
if len(history):
    st.subheader(f"Historial de la sesión ({len(history)})")
    for entry in history.items():
        tag = " · SIMULADA" if entry["simulated"] else ""
        with st.expander(f"{entry['timestamp']}{tag}"):
            st.text(entry["text"])
