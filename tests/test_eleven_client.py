import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.eleven_client import (
    DEFAULT_VOICE_ID,
    MAX_CHARS,
    MSG_API_ERROR,
    MSG_AUTH,
    MSG_CONNECTION,
    MSG_NO_KEY,
    MSG_PLAN,
    MSG_QUOTA,
    MSG_RATE,
    simulated_audio,
    synthesize_audio,
)

SECRET = "clave-secreta-456"


def fake_response(status_code=200, content=b"ID3fake-mp3", content_type="audio/mpeg", body=None):
    response = MagicMock()
    response.status_code = status_code
    response.content = content
    response.headers = {"Content-Type": content_type}
    if body is None:
        response.json.side_effect = ValueError("no JSON")
    else:
        response.json.return_value = body
    return response


def post_returning(response):
    return patch("src.eleven_client.requests.post", return_value=response)


def test_without_key_returns_simulated_wav():
    result = synthesize_audio("hola")
    assert result["simulated"] is True
    assert result["error"] == MSG_NO_KEY
    assert result["mime"] == "audio/wav"
    assert result["audio"][:4] == b"RIFF"


def test_success_with_mock():
    with post_returning(fake_response()) as post:
        result = synthesize_audio("hola", api_key=SECRET)
    assert result == {"audio": b"ID3fake-mp3", "mime": "audio/mpeg", "simulated": False, "error": None, "truncated": False}
    url = post.call_args.args[0]
    kwargs = post.call_args.kwargs
    assert url.endswith(DEFAULT_VOICE_ID)
    assert kwargs["headers"]["xi-api-key"] == SECRET
    assert kwargs["json"]["text"] == "hola"
    assert kwargs["timeout"] > 0


def test_voice_id_from_env(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "voz-123")
    with post_returning(fake_response()) as post:
        synthesize_audio("hola", api_key="k")
    assert post.call_args.args[0].endswith("voz-123")


@pytest.mark.parametrize("exc, message", [
    (requests.Timeout(), MSG_CONNECTION),
    (requests.ConnectionError(), MSG_CONNECTION),
    (requests.RequestException(), MSG_API_ERROR),
])
def test_network_errors_fall_back(exc, message):
    with patch("src.eleven_client.requests.post", side_effect=exc):
        result = synthesize_audio("hola", api_key="k")
    assert result["simulated"] is True and result["error"] == message


@pytest.mark.parametrize("status, body, message", [
    (401, {"detail": {"status": "invalid_api_key", "message": "Invalid API key"}}, MSG_AUTH),
    (401, {"detail": {"status": "quota_exceeded", "message": "This request exceeds your quota."}}, MSG_QUOTA),
    (402, {"detail": {"status": "payment_required", "message": "Paid plan required"}}, MSG_PLAN),
    (429, {"detail": {"status": "too_many_concurrent_requests"}}, MSG_RATE),
    (500, None, MSG_API_ERROR),
    (422, {"detail": [{"msg": "field required"}]}, MSG_API_ERROR),
])
def test_http_errors_fall_back_with_specific_message(status, body, message):
    response = fake_response(status_code=status, content=json.dumps(body).encode(), content_type="application/json", body=body)
    with post_returning(response):
        result = synthesize_audio("hola", api_key=SECRET)
    assert result["simulated"] is True and result["error"] == message
    assert SECRET not in result["error"]


def test_non_audio_response_falls_back():
    with post_returning(fake_response(content=b"<html>", content_type="text/html")):
        result = synthesize_audio("hola", api_key="k")
    assert result["simulated"] is True and result["error"] == MSG_API_ERROR


def test_long_text_is_truncated_and_flagged():
    with post_returning(fake_response()) as post:
        result = synthesize_audio("a" * 10_000, api_key="k")
    assert len(post.call_args.kwargs["json"]["text"]) == MAX_CHARS
    assert result["truncated"] is True


def test_error_logs_do_not_expose_key(caplog):
    with patch("src.eleven_client.requests.post", side_effect=requests.ConnectionError(f"fallo {SECRET}")):
        synthesize_audio("hola", api_key=SECRET)
    assert SECRET not in caplog.text


def test_simulated_audio_is_valid_wav():
    audio = simulated_audio(seconds=0.1)
    assert audio[:4] == b"RIFF" and audio[8:12] == b"WAVE"
