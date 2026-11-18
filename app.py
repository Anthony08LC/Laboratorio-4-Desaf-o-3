"""Analista ejecutivo de datos con voz — interfaz Streamlit.

Ejecutar: streamlit run app.py
"""
import io
import logging
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from data.generate_sample import OUTPUT as SAMPLE_PATH, generate as generate_sample
from src.eleven_client import MAX_CHARS, synthesize_audio
from src.gemini_client import format_report, generate_summary, speech_text
from src.kpis import KPI_DEFINITIONS, MIN_ROWS, REQUIRED_COLUMNS, aggregate_for_gemini, compute_kpis, format_kpi, validate_csv
from src.session import SessionHistory
from src.visuals import category_figure, fig_to_png, timeseries_figure

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("app")

MAX_FILE_MB = 10
SIMULATED = ":orange[**SIMULADO**]"

st.set_page_config(page_title="Analista ejecutivo de datos", page_icon="📊", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = SessionHistory()
if "last" not in st.session_state:
    st.session_state.last = None

st.title("Analista ejecutivo de datos con voz")
st.caption(
    "Carga un CSV de ventas: Python valida los datos y calcula los indicadores, "
    "Gemini redacta la interpretación y ElevenLabs la convierte en audio."
)

# --- Barra lateral: datos y estado de los servicios ---------------------------------
with st.sidebar:
    st.header("Datos")
    uploaded = st.file_uploader("Archivo CSV de ventas", type=["csv"], help=f"Máximo {MAX_FILE_MB} MB.")
    use_sample = st.checkbox("Usar datos de ejemplo", help="data/sample_sales.csv: 200 pedidos sintéticos.")
    st.caption(f"Columnas obligatorias: {', '.join(REQUIRED_COLUMNS)} · mínimo {MIN_ROWS} filas válidas.")

    st.header("Servicios")
    for key, service in (("GEMINI_API_KEY", "Gemini"), ("ELEVENLABS_API_KEY", "ElevenLabs")):
        if os.getenv(key, "").strip():
            st.success(f"{service}: clave configurada")
        else:
            st.warning(f"{service}: clave no configurada · se usará una respuesta SIMULADA")
    st.caption("Privacidad: a Gemini solo se envían estadísticas agregadas, nunca filas del CSV. No subas datos personales.")

source = None
if uploaded is not None:
    if uploaded.size > MAX_FILE_MB * 1024 * 1024:
        st.error(f"El archivo supera el máximo de {MAX_FILE_MB} MB.")
        st.stop()
    source = io.BytesIO(uploaded.getvalue())
elif use_sample:
    if not Path(SAMPLE_PATH).exists():
        generate_sample()
    source = str(SAMPLE_PATH)

if source is None:
    st.info("Carga un archivo CSV o marca **Usar datos de ejemplo** en la barra lateral para comenzar.")
    st.dataframe(
        pd.DataFrame({
            "Columna": REQUIRED_COLUMNS,
            "Tipo": ["texto único", "fecha AAAA-MM-DD", "texto", "entero ≥ 1", "número ≥ 0", "1/0, true/false, sí/no"],
            "Ejemplo": ["ORD-0001", "2026-01-15", "Hogar", "2", "59.90", "1"],
        }),
        hide_index=True,
    )
    st.stop()

# --- Validación y calidad de datos ------------------------------------------------
try:
    df = validate_csv(source)
except ValueError as exc:
    st.error(f"El archivo no cumple los requisitos. {exc}")
    st.stop()
except Exception:  # cualquier fallo inesperado se muestra sin cerrar la app
    logger.exception("Error inesperado al procesar el CSV")
    st.error("Ocurrió un error inesperado al procesar el archivo. Revisa que sea un CSV de ventas válido.")
    st.stop()

quality = df.attrs["quality"]
st.success(f"Archivo válido: {quality['rows_valid']} filas analizadas de {quality['rows_read']} leídas.")
if quality["dropped_rows"]:
    detail = ", ".join(f"{col}: {n}" for col, n in quality["missing"].items())
    st.warning(f"Se descartaron {quality['dropped_rows']} fila(s) con valores obligatorios vacíos. Celdas vacías por columna — {detail}.")
elif quality["missing"]:
    st.info(f"Categorías vacías reemplazadas por «Sin categoría»: {quality['missing'].get('category', 0)}.")
with st.expander("Calidad y vista previa de los datos"):
    st.dataframe(
        pd.DataFrame({"Columna": REQUIRED_COLUMNS, "Celdas vacías": [quality["missing"].get(c, 0) for c in REQUIRED_COLUMNS]}),
        hide_index=True,
    )
    st.dataframe(df.head(10), hide_index=True)

# --- KPI --------------------------------------------------------------------------
kpis = compute_kpis(df)
st.subheader("Indicadores clave")
st.caption("Calculados con Python sobre las filas válidas. Pasa el cursor por cada indicador para ver su fórmula.")
cols = st.columns(4)
for i, (name, definition) in enumerate(KPI_DEFINITIONS.items()):
    cols[i % 4].metric(
        definition["label"], format_kpi(name, kpis[name]), border=True,
        help=f"{definition['description']} Fórmula: {definition['formula']}",
    )
with st.expander("Definición y fórmula de cada indicador"):
    st.dataframe(
        pd.DataFrame([
            {"Indicador": d["label"], "Valor": format_kpi(n, kpis[n]), "Fórmula": d["formula"], "Descripción": d["description"]}
            for n, d in KPI_DEFINITIONS.items()
        ]),
        hide_index=True,
    )

# --- Visualizaciones ----------------------------------------------------------------
st.subheader("Visualizaciones")
left, right = st.columns(2)
for column, fig_builder, label, filename in (
    (left, timeseries_figure, "Descargar gráfico (PNG)", "evolucion_ventas.png"),
    (right, category_figure, "Descargar gráfico (PNG)", "ventas_categoria.png"),
):
    with column.container(border=True):
        png = fig_to_png(fig_builder(df))
        st.image(png)
        st.download_button(label, png, file_name=filename, mime="image/png", key=filename)
st.caption("Solo se suman las compras (is_purchase = 1). Los periodos sin compras se muestran con ventas = 0.")

# --- Resumen ejecutivo, recomendaciones y audio --------------------------------------
st.subheader("Resumen ejecutivo")
stats = aggregate_for_gemini(df)
with st.expander("Estadísticas agregadas que se envían a Gemini"):
    st.code(stats, language=None)

if st.button("Generar resumen ejecutivo y audio", type="primary"):
    with st.spinner("Generando resumen con Gemini..."):
        summary = generate_summary(stats)
    with st.spinner("Generando audio con ElevenLabs..."):
        audio = synthesize_audio(speech_text(summary))
    st.session_state.history.add(format_report(summary), summary["simulated"], audio["simulated"])
    st.session_state.last = {"stats": stats, "summary": summary, "audio": audio}

last = st.session_state.last
if last and last["stats"] != stats:
    st.info("El último resumen corresponde a otro archivo. Pulsa el botón para generar uno con los datos actuales.")
elif last:
    summary, audio = last["summary"], last["audio"]
    for message in (summary["error"], summary["warning"], audio["error"]):
        if message:
            st.warning(message)

    origin = f"{SIMULATED} — texto de demostración, sin Gemini" if summary["simulated"] else "Interpretación generada por Gemini"
    st.markdown(f"Origen del texto: {origin}. Las cifras de los indicadores provienen de Python.")
    summary_col, reco_col = st.columns(2)
    with summary_col.container(border=True):
        st.markdown("#### Resumen")
        st.write(summary["summary"])
        st.markdown("#### Hallazgos")
        st.markdown("\n".join(f"- {item}" for item in summary["findings"]))
    with reco_col.container(border=True):
        st.markdown("#### Recomendaciones")
        st.markdown("\n".join(f"{i}. {item}" for i, item in enumerate(summary["recommendations"], 1)))

    with st.container(border=True):
        if audio["simulated"]:
            st.markdown(f"#### Audio {SIMULATED}\nTono de prueba local: **no** es una voz generada por ElevenLabs.")
        else:
            st.markdown("#### Audio del resumen (ElevenLabs)")
        st.audio(audio["audio"], format=audio["mime"])
        if audio["truncated"]:
            st.caption(f"El texto superó {MAX_CHARS} caracteres; el audio narra solo la primera parte.")
    st.download_button("Exportar resumen (.txt)", format_report(summary), file_name="resumen_ejecutivo.txt", mime="text/plain")

history = st.session_state.history
if len(history):
    st.subheader(f"Historial de la sesión ({len(history)})")
    for entry in history.items():
        tag = "".join((" · texto SIMULADO" if entry["simulated"] else "", " · audio SIMULADO" if entry["audio_simulated"] else ""))
        with st.expander(f"{entry['timestamp']}{tag}"):
            st.text(entry["text"])
