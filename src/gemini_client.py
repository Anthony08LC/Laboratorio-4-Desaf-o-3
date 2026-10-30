"""Cliente de Gemini con fallback a resumen SIMULADO."""
import hashlib
import logging
import os
from pathlib import Path
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)

TEMPLATE_PATH = Path(__file__).parent / "prompts" / "summary_template.txt"
DEFAULT_MODEL = "gemini-2.5-flash"
TIMEOUT_MS = 30_000
REQUIRED_SECTIONS = ["cálculos verificables", "interpretación", "recomendaciones"]

MSG_NO_KEY = "Clave de Gemini no configurada. Usando respuesta simulada marcada como SIMULADA."
MSG_API_ERROR = "Error al comunicarse con Gemini. Intenta de nuevo más tarde. Mostrando respuesta simulada."
MSG_BAD_FORMAT = "La respuesta del modelo no cumple el formato esperado; revise los logs."


def load_template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def simulated_summary(aggregated_stats: str) -> str:
    return (
        "[SIMULADA] Resumen generado localmente sin Gemini.\n\n"
        "Cálculos verificables:\n"
        f"{aggregated_stats}\n\n"
        "Interpretación:\n"
        "Texto de demostración: no se realizó interpretación con un modelo de lenguaje.\n\n"
        "Recomendaciones:\n"
        "- Configurar GEMINI_API_KEY para obtener recomendaciones reales.\n"
        "- Revisar los KPIs y gráficos mostrados en la aplicación."
    )


def has_required_sections(text: str) -> bool:
    lowered = text.lower()
    return all(section in lowered for section in REQUIRED_SECTIONS)


def _default_client_factory(api_key: str):
    from google import genai
    from google.genai import types

    return genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=TIMEOUT_MS))


def generate_summary(
    aggregated_stats: str,
    prompt_template: Optional[str] = None,
    *,
    api_key: Optional[str] = None,
    client_factory: Optional[Callable] = None,
) -> Dict:
    """Devuelve {"text", "simulated", "error", "warning"}; nunca lanza excepciones."""
    api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY", "")
    template = prompt_template or load_template()
    stats_hash = hashlib.sha256(aggregated_stats.encode("utf-8")).hexdigest()[:12]

    if not api_key.strip():
        logger.info("Gemini sin clave; resumen simulado (stats=%s)", stats_hash)
        return {"text": simulated_summary(aggregated_stats), "simulated": True, "error": MSG_NO_KEY, "warning": None}

    model = os.getenv("GEMINI_MODEL", "") or DEFAULT_MODEL
    try:
        client = (client_factory or _default_client_factory)(api_key)
        logger.info("Solicitud a Gemini model=%s stats=%s", model, stats_hash)
        response = client.models.generate_content(model=model, contents=template.format(stats=aggregated_stats))
        text = (getattr(response, "text", None) or "").strip()
    except Exception as exc:  # red, timeout, cuota, credenciales
        logger.warning("Fallo en Gemini (stats=%s): %s", stats_hash, type(exc).__name__)
        return {"text": simulated_summary(aggregated_stats), "simulated": True, "error": MSG_API_ERROR, "warning": None}

    if not text:
        logger.warning("Gemini devolvió respuesta vacía (stats=%s)", stats_hash)
        return {"text": simulated_summary(aggregated_stats), "simulated": True, "error": MSG_API_ERROR, "warning": None}

    warning = None
    if not has_required_sections(text):
        logger.warning("Respuesta de Gemini sin secciones requeridas (stats=%s): %r", stats_hash, text[:200])
        warning = MSG_BAD_FORMAT
    return {"text": text, "simulated": False, "error": None, "warning": warning}
