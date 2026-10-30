from types import SimpleNamespace
from unittest.mock import patch

from src import gemini_client
from src.gemini_client import MSG_API_ERROR, MSG_BAD_FORMAT, MSG_NO_KEY, generate_summary, load_template

STATS = "Ventas totales: 100.00\nCompras: 5"
GOOD_TEXT = "Cálculos verificables:\n- Ventas 100\n\nInterpretación:\n- ok\n\nRecomendaciones:\n- hacer X"


class FakeClient:
    def __init__(self, text=None, exc=None):
        self.calls = []
        self.models = SimpleNamespace(generate_content=self._generate)
        self._text, self._exc = text, exc

    def _generate(self, model, contents):
        self.calls.append((model, contents))
        if self._exc:
            raise self._exc
        return SimpleNamespace(text=self._text)


def test_without_key_returns_simulated():
    result = generate_summary(STATS)
    assert result["simulated"] is True
    assert result["error"] == MSG_NO_KEY
    assert "[SIMULADA]" in result["text"]
    assert gemini_client.has_required_sections(result["text"])


def test_success_with_mock_client():
    fake = FakeClient(text=GOOD_TEXT)
    result = generate_summary(STATS, api_key="test-key", client_factory=lambda key: fake)
    assert result == {"text": GOOD_TEXT, "simulated": False, "error": None, "warning": None}
    model, prompt = fake.calls[0]
    assert model == gemini_client.DEFAULT_MODEL
    assert STATS in prompt and "{stats}" not in prompt


def test_model_from_env(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "otro-modelo")
    fake = FakeClient(text=GOOD_TEXT)
    generate_summary(STATS, api_key="k", client_factory=lambda key: fake)
    assert fake.calls[0][0] == "otro-modelo"


def test_network_error_falls_back():
    fake = FakeClient(exc=TimeoutError("timeout"))
    result = generate_summary(STATS, api_key="k", client_factory=lambda key: fake)
    assert result["simulated"] is True
    assert result["error"] == MSG_API_ERROR


def test_client_creation_error_falls_back():
    def broken_factory(key):
        raise RuntimeError("credenciales inválidas")

    result = generate_summary(STATS, api_key="k", client_factory=broken_factory)
    assert result["simulated"] is True and result["error"] == MSG_API_ERROR


def test_empty_response_falls_back():
    result = generate_summary(STATS, api_key="k", client_factory=lambda key: FakeClient(text=None))
    assert result["simulated"] is True and result["error"] == MSG_API_ERROR


def test_bad_format_is_flagged():
    result = generate_summary(STATS, api_key="k", client_factory=lambda key: FakeClient(text="Todo bien."))
    assert result["simulated"] is False
    assert result["warning"] == MSG_BAD_FORMAT


def test_key_from_env_uses_default_factory(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env-key")
    fake = FakeClient(text=GOOD_TEXT)
    with patch.object(gemini_client, "_default_client_factory", return_value=fake) as factory:
        result = generate_summary(STATS)
    factory.assert_called_once_with("env-key")
    assert result["simulated"] is False


def test_default_factory_builds_real_client_offline():
    client = gemini_client._default_client_factory("dummy-key")
    assert hasattr(client.models, "generate_content")


def test_template_has_placeholder_and_sections():
    template = load_template()
    assert "{stats}" in template
    assert gemini_client.has_required_sections(template)
