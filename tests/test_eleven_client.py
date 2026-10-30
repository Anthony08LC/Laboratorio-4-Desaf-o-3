from unittest.mock import MagicMock, patch

import requests

from src.eleven_client import DEFAULT_VOICE_ID, MSG_API_ERROR, MSG_NO_KEY, simulated_audio, synthesize_audio


def fake_response(content=b"ID3fake-mp3", content_type="audio/mpeg", status_error=None):
    response = MagicMock()
    response.content = content
    response.headers = {"Content-Type": content_type}
    response.raise_for_status.side_effect = status_error
    return response


def test_without_key_returns_simulated_wav():
    result = synthesize_audio("hola")
    assert result["simulated"] is True
    assert result["error"] == MSG_NO_KEY
    assert result["mime"] == "audio/wav"
    assert result["audio"][:4] == b"RIFF"


def test_success_with_mock():
    with patch("src.eleven_client.requests.post", return_value=fake_response()) as post:
        result = synthesize_audio("hola", api_key="test-key")
    assert result == {"audio": b"ID3fake-mp3", "mime": "audio/mpeg", "simulated": False, "error": None}
    url = post.call_args.args[0]
    kwargs = post.call_args.kwargs
    assert url.endswith(DEFAULT_VOICE_ID)
    assert kwargs["headers"]["xi-api-key"] == "test-key"
    assert kwargs["json"]["text"] == "hola"
    assert kwargs["timeout"] > 0


def test_voice_id_from_env(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "voz-123")
    with patch("src.eleven_client.requests.post", return_value=fake_response()) as post:
        synthesize_audio("hola", api_key="k")
    assert post.call_args.args[0].endswith("voz-123")


def test_timeout_falls_back():
    with patch("src.eleven_client.requests.post", side_effect=requests.Timeout()):
        result = synthesize_audio("hola", api_key="k")
    assert result["simulated"] is True and result["error"] == MSG_API_ERROR


def test_http_error_falls_back():
    error = requests.HTTPError("401 Unauthorized")
    with patch("src.eleven_client.requests.post", return_value=fake_response(status_error=error)):
        result = synthesize_audio("hola", api_key="k")
    assert result["simulated"] is True and result["error"] == MSG_API_ERROR


def test_non_audio_response_falls_back():
    response = fake_response(content=b'{"detail":"quota"}', content_type="application/json")
    with patch("src.eleven_client.requests.post", return_value=response):
        result = synthesize_audio("hola", api_key="k")
    assert result["simulated"] is True and result["error"] == MSG_API_ERROR


def test_long_text_is_truncated():
    with patch("src.eleven_client.requests.post", return_value=fake_response()) as post:
        synthesize_audio("a" * 10_000, api_key="k")
    assert len(post.call_args.kwargs["json"]["text"]) == 2500


def test_simulated_audio_is_valid_wav():
    audio = simulated_audio(seconds=0.1)
    assert audio[:4] == b"RIFF" and audio[8:12] == b"WAVE"
