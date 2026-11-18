"""Cliente de ElevenLabs (API REST oficial de text-to-speech) con fallback a audio SIMULADO.

El audio simulado es un tono WAV local: nunca se presenta como voz generada por ElevenLabs.
"""
import io
import logging
import math
import os
import struct
import wave
from typing import Dict, Optional

import requests

logger = logging.getLogger(__name__)

API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
MODEL_ID = "eleven_multilingual_v2"
TIMEOUT_S = 30
MAX_CHARS = 2500  # protege la cuota del plan gratuito

_FALLBACK = "Se reproduce un tono SIMULADO en su lugar."
MSG_NO_KEY = f"Clave de ElevenLabs no configurada (ELEVENLABS_API_KEY). {_FALLBACK}"
MSG_AUTH = f"ElevenLabs rechazó la clave de API: revisa ELEVENLABS_API_KEY en .env. {_FALLBACK}"
MSG_QUOTA = f"Se agotaron los créditos de ElevenLabs de tu plan. {_FALLBACK}"
MSG_PLAN = f"La voz configurada requiere un plan de pago de ElevenLabs: usa otra ELEVENLABS_VOICE_ID. {_FALLBACK}"
MSG_RATE = f"ElevenLabs alcanzó su límite de solicitudes; espera unos segundos y reintenta. {_FALLBACK}"
MSG_CONNECTION = f"No se pudo conectar con ElevenLabs (red o tiempo de espera agotado). {_FALLBACK}"
MSG_API_ERROR = f"Error al comunicarse con ElevenLabs. Intenta de nuevo más tarde. {_FALLBACK}"


def simulated_audio(seconds: float = 1.5, freq: float = 440.0, rate: int = 16000) -> bytes:
    """Tono WAV corto que indica que el audio es una simulación."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        frames = b"".join(
            struct.pack("<h", int(8000 * math.sin(2 * math.pi * freq * i / rate)))
            for i in range(int(seconds * rate))
        )
        wav.writeframes(frames)
    return buffer.getvalue()


def _fallback(error: str, truncated: bool = False) -> Dict:
    return {"audio": simulated_audio(), "mime": "audio/wav", "simulated": True, "error": error, "truncated": truncated}


def _http_error_message(response) -> str:
    try:
        detail = response.json().get("detail", {})
        status = detail.get("status", "") if isinstance(detail, dict) else ""
    except (ValueError, AttributeError):
        status = ""
    if status == "quota_exceeded":
        return MSG_QUOTA
    if response.status_code == 401:
        return MSG_AUTH
    if response.status_code == 402:
        return MSG_PLAN
    if response.status_code == 429:
        return MSG_RATE
    return MSG_API_ERROR


def synthesize_audio(text: str, *, api_key: Optional[str] = None, voice_id: Optional[str] = None) -> Dict:
    """Devuelve {"audio": bytes, "mime", "simulated", "error", "truncated"}; nunca lanza excepciones."""
    api_key = (api_key if api_key is not None else os.getenv("ELEVENLABS_API_KEY", "")).strip()
    truncated = len(text) > MAX_CHARS
    if not api_key:
        logger.info("ElevenLabs sin clave; audio simulado")
        return _fallback(MSG_NO_KEY, truncated)

    voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID", "").strip() or DEFAULT_VOICE_ID
    try:
        logger.info("Solicitud a ElevenLabs voice=%s chars=%d", voice_id, min(len(text), MAX_CHARS))
        response = requests.post(
            API_URL.format(voice_id=voice_id),
            headers={"xi-api-key": api_key, "Accept": "audio/mpeg"},
            json={"text": text[:MAX_CHARS], "model_id": MODEL_ID},
            timeout=TIMEOUT_S,
        )
    except (requests.ConnectionError, requests.Timeout) as exc:
        logger.warning("Fallo de conexión con ElevenLabs: %s", type(exc).__name__)
        return _fallback(MSG_CONNECTION, truncated)
    except requests.RequestException as exc:
        logger.warning("Fallo en ElevenLabs: %s", type(exc).__name__)
        return _fallback(MSG_API_ERROR, truncated)

    if response.status_code != 200:
        logger.warning("ElevenLabs respondió HTTP %s", response.status_code)
        return _fallback(_http_error_message(response), truncated)
    content_type = response.headers.get("Content-Type", "")
    if not response.content or not content_type.startswith("audio/"):
        logger.warning("Respuesta inesperada de ElevenLabs: Content-Type=%s", content_type)
        return _fallback(MSG_API_ERROR, truncated)
    return {"audio": response.content, "mime": "audio/mpeg", "simulated": False, "error": None, "truncated": truncated}
