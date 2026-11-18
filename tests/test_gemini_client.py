import json
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import pytest
from google.genai import errors

from src import gemini_client
from src.gemini_client import (
    MSG_API_ERROR,
    MSG_AUTH,
    MSG_BAD_FORMAT,
    MSG_CONNECTION,
    MSG_MODEL,
    MSG_NO_KEY,
    MSG_QUOTA,
    format_report,
    generate_summary,
    load_template,
    speech_text,
    unverified_numbers,
)

STATS = "Ventas totales: 22,677.71\nCompras: 119\nTasa de conversión: 59.5%"
GOOD = {
    "resumen": "Las ventas totales fueron 22,677.71 con una conversión de 59.5%.",
    "hallazgos": ["Se registraron 119 compras.", "La conversión supera la mitad de las transacciones."],
    "recomendaciones": ["Reforzar la categoría líder.", "Analizar las transacciones no convertidas."],
}
SECRET = "clave-secreta-123"


class FakeClient:
    def __init__(self, text=None, exc=None):
        self.calls = []
        self.models = SimpleNamespace(generate_content=self._generate)
        self._text, self._exc = text, exc

    def _generate(self, model, contents, config=None):
        self.calls.append({"model": model, "contents": contents, "config": config})
        if self._exc:
            raise self._exc
        return SimpleNamespace(text=self._text)


def run(text=None, exc=None, **kwargs):
    fake = FakeClient(text=text, exc=exc)
    return generate_summary(STATS, api_key=SECRET, client_factory=lambda key: fake, **kwargs), fake


def api_error(cls, code, status, message):
    return cls(code, {"error": {"code": code, "status": status, "message": message}})


def test_without_key_returns_simulated():
    result = generate_summary(STATS)
    assert result["simulated"] is True
    assert result["error"] == MSG_NO_KEY
    assert result["facts"] == STATS
    assert all("[SIMULADA]" in t for t in [result["summary"], *result["findings"], *result["recommendations"]])


def test_blank_key_is_treated_as_missing():
    assert generate_summary(STATS, api_key="   ")["error"] == MSG_NO_KEY


def test_success_with_mock_client():
    result, fake = run(json.dumps(GOOD))
    assert result == {
        "facts": STATS, "summary": GOOD["resumen"], "findings": GOOD["hallazgos"],
        "recommendations": GOOD["recomendaciones"], "simulated": False, "error": None, "warning": None,
    }
    call = fake.calls[0]
    assert call["model"] == gemini_client.DEFAULT_MODEL
    assert STATS in call["contents"] and "{stats}" not in call["contents"]
    assert call["config"].response_mime_type == "application/json"


def test_only_aggregated_stats_are_sent(sample_csv):
    from src.kpis import aggregate_for_gemini, validate_csv

    df = validate_csv(str(sample_csv))
    fake = FakeClient(text=json.dumps(GOOD))
    generate_summary(aggregate_for_gemini(df), api_key="k", client_factory=lambda key: fake)
    prompt = fake.calls[0]["contents"]
    assert "ORD-" not in prompt
    assert len(prompt) < len(load_template()) + 1000


def test_model_from_env(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "otro-modelo")
    _, fake = run(json.dumps(GOOD))
    assert fake.calls[0]["model"] == "otro-modelo"


@pytest.mark.parametrize("exc, message", [
    (api_error(errors.ClientError, 429, "RESOURCE_EXHAUSTED", "Resource has been exhausted (e.g. check quota)."), MSG_QUOTA),
    (api_error(errors.ClientError, 400, "INVALID_ARGUMENT", "API key not valid. Please pass a valid API key."), MSG_AUTH),
    (api_error(errors.ClientError, 403, "PERMISSION_DENIED", "Permission denied."), MSG_AUTH),
    (api_error(errors.ClientError, 404, "NOT_FOUND", "models/x is not found."), MSG_MODEL),
    (api_error(errors.ServerError, 503, "UNAVAILABLE", "The model is overloaded."), MSG_API_ERROR),
    (httpx.ConnectError("sin red"), MSG_CONNECTION),
    (httpx.ReadTimeout("timeout"), MSG_CONNECTION),
    (TimeoutError("timeout"), MSG_CONNECTION),
    (RuntimeError("otro"), MSG_API_ERROR),
])
def test_api_errors_fall_back_with_specific_message(exc, message):
    result, _ = run(exc=exc)
    assert result["simulated"] is True
    assert result["error"] == message
    assert SECRET not in json.dumps(result, ensure_ascii=False)


def test_client_creation_error_falls_back():
    def broken_factory(key):
        raise RuntimeError("credenciales inválidas")

    result = generate_summary(STATS, api_key="k", client_factory=broken_factory)
    assert result["simulated"] is True and result["error"] == MSG_API_ERROR


def test_error_logs_do_not_expose_key(caplog):
    run(exc=RuntimeError(f"fallo con {SECRET}"))
    assert SECRET not in caplog.text


@pytest.mark.parametrize("text", [
    None,
    "Todo bien.",
    json.dumps({"resumen": "x"}),
    json.dumps({**GOOD, "recomendaciones": []}),
    json.dumps({**GOOD, "resumen": "  "}),
])
def test_bad_format_falls_back(text):
    result, _ = run(text)
    assert result["simulated"] is True
    assert result["error"] == MSG_BAD_FORMAT


def test_invented_numbers_are_flagged():
    invented = {**GOOD, "hallazgos": ["Las ventas crecieron 15.3% y llegaron a 30,000 en marzo."]}
    result, _ = run(json.dumps(invented))
    assert result["simulated"] is False
    assert "15.3" in result["warning"] and "30000" in result["warning"]


def test_unverified_numbers_accepts_rounding_and_exact_copies():
    assert unverified_numbers("Ventas de 22,677.71 (unos 22,678) y 119 compras; conversión 59.5%.", STATS) == []
    assert unverified_numbers("Se vendieron 500 unidades.", STATS) == ["500"]


def test_key_from_env_uses_default_factory(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env-key")
    fake = FakeClient(text=json.dumps(GOOD))
    with patch.object(gemini_client, "_default_client_factory", return_value=fake) as factory:
        result = generate_summary(STATS)
    factory.assert_called_once_with("env-key")
    assert result["simulated"] is False


def test_default_factory_builds_real_client_offline():
    client = gemini_client._default_client_factory("dummy-key")
    assert hasattr(client.models, "generate_content")


def test_template_has_placeholder_and_rules():
    template = load_template()
    assert "{stats}" in template
    for key in ('"resumen"', '"hallazgos"', '"recomendaciones"', "No inventes cifras"):
        assert key in template


def test_report_separates_calculated_data_from_interpretation():
    result, _ = run(json.dumps(GOOD))
    report = format_report(result)
    assert "DATOS CALCULADOS (Python, verificables)\n" + STATS in report
    assert "HALLAZGOS (interpretación generada por Gemini)" in report
    assert "RECOMENDACIONES" in report
    assert "SIMULADA" in format_report(generate_summary(STATS))


def test_speech_text_excludes_raw_stats_and_marks_simulation():
    text = speech_text(generate_summary(STATS))
    assert text.startswith("Resumen ejecutivo.")
    assert "Recomendaciones." in text and "Simulado:" in text and "[SIMULADA]" not in text
    assert "Tasa de conversión" not in text
