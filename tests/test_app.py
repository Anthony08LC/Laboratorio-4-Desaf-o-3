"""Pruebas de integración de la interfaz con streamlit.testing (sin claves → modo SIMULADO)."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.kpis import KPI_DEFINITIONS

APP = str(Path(__file__).parent.parent / "app.py")


def run_app():
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    return at


def run_with_sample():
    at = run_app()
    at.sidebar.checkbox[0].check().run()
    return at


def test_initial_screen_shows_key_warnings_and_format():
    at = run_app()
    assert not at.exception
    warnings = [w.value for w in at.sidebar.warning]
    assert any("Gemini: clave no configurada" in w for w in warnings)
    assert any("ElevenLabs: clave no configurada" in w for w in warnings)
    assert "Carga un archivo CSV" in at.info[0].value


def test_sample_shows_kpis_and_charts():
    at = run_with_sample()
    assert not at.exception
    assert "Archivo válido: 200 filas analizadas" in at.success[0].value
    # AppTest recorre la cuadrícula columna por columna, por eso se compara el conjunto.
    assert sorted(m.label for m in at.metric) == sorted(d["label"] for d in KPI_DEFINITIONS.values())
    assert any(s.value == "Visualizaciones" for s in at.subheader)


def test_end_to_end_with_simulated_apis():
    at = run_with_sample()
    at.button[0].click().run()
    assert not at.exception
    warnings = " ".join(w.value for w in at.warning)
    assert "Clave de Gemini no configurada" in warnings
    assert "Clave de ElevenLabs no configurada" in warnings
    markdown = " ".join(m.value for m in at.markdown)
    assert "SIMULADO" in markdown and "#### Recomendaciones" in markdown
    assert "no** es una voz generada por ElevenLabs" in markdown


def test_history_keeps_at_most_five():
    at = run_with_sample()
    for _ in range(6):
        at.button[0].click().run()
    assert not at.exception
    assert len(at.session_state.history) == 5
    assert any("Historial de la sesión (5)" in s.value for s in at.subheader)
