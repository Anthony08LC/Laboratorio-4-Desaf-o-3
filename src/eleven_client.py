"""Cliente de ElevenLabs (TTS) con fallback a audio SIMULADO (tono WAV local)."""
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

MSG_NO_KEY = "Clave de ElevenLabs no configurada. Usando respuesta simulada marcada como SIMULADA."
MSG_API_ERROR = "Error al comunicarse con ElevenLabs. Intenta de nuevo más tarde. Mostrando respuesta simulada."


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


def _fallback(error: str) -> Dict:
    return {"audio": simulated_audio(), "mime": "audio/wav", "simulated": True, "error": error}


def synthesize_audio(text: str, *, api_key: Optional[str] = None, voice_id: Optional[str] = None) -> Dict:
    """Devuelve {"audio": bytes, "mime", "simulated", "error"}; nunca lanza excepciones."""
    api_key = api_key if api_key is not None else os.getenv("ELEVENLABS_API_KEY", "")
    if not api_key.strip():
        logger.info("ElevenLabs sin clave; audio simulado")
        return _fallback(MSG_NO_KEY)

    voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID", "") or DEFAULT_VOICE_ID
    try:
        logger.info("Solicitud a ElevenLabs voice=%s chars=%d", voice_id, len(text))
        response = requests.post(
            API_URL.format(voice_id=voice_id),
            headers={"xi-api-key": api_key, "Accept": "audio/mpeg"},
            json={"text": text[:MAX_CHARS], "model_id": MODEL_ID},
            timeout=TIMEOUT_S,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Fallo en ElevenLabs: %s", type(exc).__name__)
        return _fallback(MSG_API_ERROR)

    content_type = response.headers.get("Content-Type", "")
    if not response.content or not content_type.startswith("audio/"):
        logger.warning("Respuesta inesperada de ElevenLabs: Content-Type=%s", content_type)
        return _fallback(MSG_API_ERROR)
    return {"audio": response.content, "mime": "audio/mpeg", "simulated": False, "error": None}
