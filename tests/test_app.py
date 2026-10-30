"""Pruebas de integración de la interfaz con streamlit.testing (sin claves → modo SIMULADA)."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).parent.parent / "app.py")


def run_app():
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    return at


def test_initial_screen_shows_key_warnings():
    at = run_app()
    assert not at.exception
    warnings = [w.value for w in at.warning]
    assert any("Gemini no configurada" in w for w in warnings)
    assert any("ElevenLabs no configurada" in w for w in warnings)


def test_end_to_end_with_sample_and_simulated_apis():
    at = run_app()
    at.checkbox[0].check().run()
    assert not at.exception
    assert "CSV válido" in at.success[0].value
    assert len(at.metric) == 7

    at.button[0].click().run()
    assert not at.exception
    texts = [t.value for t in at.text]
    assert any("[SIMULADA]" in t and "Recomendaciones" in t for t in texts)
    assert any("SIMULADA" in m.value for m in at.markdown)


def test_history_keeps_at_most_five():
    at = run_app()
    at.checkbox[0].check().run()
    for _ in range(6):
        at.button[0].click().run()
    assert not at.exception
    assert len(at.session_state.history) == 5
    assert any("Historial de la sesión (5)" in s.value for s in at.subheader)
