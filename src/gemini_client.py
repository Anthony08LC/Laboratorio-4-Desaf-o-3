"""Cliente de Gemini (SDK google-genai) con fallback a resumen SIMULADO.

Gemini solo recibe el texto de estadísticas agregadas y devuelve interpretación
(resumen, hallazgos, recomendaciones). Los datos calculados nunca los redacta el modelo.
"""
import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

TEMPLATE_PATH = Path(__file__).parent / "prompts" / "summary_template.txt"
DEFAULT_MODEL = "gemini-3.6-flash"
TIMEOUT_MS = 60_000
RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "resumen": {"type": "STRING"},
        "hallazgos": {"type": "ARRAY", "items": {"type": "STRING"}},
        "recomendaciones": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["resumen", "hallazgos", "recomendaciones"],
}

_FALLBACK = "Mostrando respuesta simulada."
MSG_NO_KEY = f"Clave de Gemini no configurada (GEMINI_API_KEY). {_FALLBACK}"
MSG_AUTH = f"Gemini rechazó la clave de API: revisa GEMINI_API_KEY en .env. {_FALLBACK}"
MSG_QUOTA = f"Cuota o límite de solicitudes de Gemini agotado. Espera unos minutos o revisa tu plan. {_FALLBACK}"
MSG_MODEL = f"El modelo de Gemini configurado no está disponible: revisa GEMINI_MODEL en .env. {_FALLBACK}"
MSG_CONNECTION = f"No se pudo conectar con Gemini (red o tiempo de espera agotado). {_FALLBACK}"
MSG_API_ERROR = f"Error al comunicarse con Gemini. Intenta de nuevo más tarde. {_FALLBACK}"
MSG_BAD_FORMAT = f"La respuesta de Gemini no cumple el formato esperado; revisa los logs. {_FALLBACK}"
MSG_UNVERIFIED = "La interpretación menciona cifras que no aparecen en los datos calculados: {numbers}. Verifícalas antes de usarlas."

_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def load_template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def _result(facts: str, summary: str, findings: List[str], recommendations: List[str], *,
            simulated: bool, error: Optional[str] = None, warning: Optional[str] = None) -> Dict:
    return {"facts": facts, "summary": summary, "findings": findings, "recommendations": recommendations,
            "simulated": simulated, "error": error, "warning": warning}


def simulated_summary(aggregated_stats: str, error: str) -> Dict:
    return _result(
        aggregated_stats,
        "[SIMULADA] Resumen generado localmente, sin Gemini. Los datos calculados son reales, "
        "pero este texto no contiene interpretación de un modelo de lenguaje.",
        ["[SIMULADA] Sin hallazgos: requieren la interpretación de Gemini."],
        ["[SIMULADA] Configura GEMINI_API_KEY en .env para obtener recomendaciones generadas por Gemini.",
         "[SIMULADA] Mientras tanto, revisa los KPI y gráficos calculados por Python."],
        simulated=True, error=error,
    )


def _numbers(text: str) -> List[str]:
    """Cifras relevantes (con decimales o ≥3 dígitos), sin separadores de miles."""
    found = (m.replace(",", "") for m in _NUMBER.findall(text))
    return [n for n in found if "." in n or len(n) >= 3]


def unverified_numbers(text: str, aggregated_stats: str) -> List[str]:
    """Cifras del texto que no coinciden (admitiendo redondeo) con ninguna de las estadísticas."""
    known = [float(n) for n in _numbers(aggregated_stats)]
    unverified = []
    for token in _numbers(text):
        decimals = len(token.split(".")[1]) if "." in token else 0
        if not any(round(value, decimals) == float(token) for value in known) and token not in unverified:
            unverified.append(token)
    return unverified


def _parse(text: str):
    data = json.loads(text)
    summary, findings, recommendations = data["resumen"], data["hallazgos"], data["recomendaciones"]
    if not (isinstance(summary, str) and summary.strip()):
        raise ValueError("resumen vacío")
    for items in (findings, recommendations):
        if not (isinstance(items, list) and items and all(isinstance(i, str) and i.strip() for i in items)):
            raise ValueError("lista vacía o inválida")
    return summary.strip(), [i.strip() for i in findings], [i.strip() for i in recommendations]


def _classify_error(exc: Exception) -> str:
    from google.genai import errors
    import httpx

    if isinstance(exc, errors.APIError):
        message = str(getattr(exc, "message", "") or "").lower()
        if exc.code == 429 or exc.status == "RESOURCE_EXHAUSTED":
            return MSG_QUOTA
        if exc.code in (401, 403) or (exc.code == 400 and "api key" in message):
            return MSG_AUTH
        if exc.code == 404:
            return MSG_MODEL
        return MSG_API_ERROR
    if isinstance(exc, (httpx.TransportError, ConnectionError, TimeoutError)):
        return MSG_CONNECTION
    return MSG_API_ERROR


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
    """Devuelve {"facts", "summary", "findings", "recommendations", "simulated", "error", "warning"}.

    Nunca lanza excepciones: ante cualquier fallo devuelve la versión SIMULADA con el motivo en "error".
    """
    api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY", "")
    template = prompt_template or load_template()
    stats_hash = hashlib.sha256(aggregated_stats.encode("utf-8")).hexdigest()[:12]

    if not api_key.strip():
        logger.info("Gemini sin clave; resumen simulado (stats=%s)", stats_hash)
        return simulated_summary(aggregated_stats, MSG_NO_KEY)

    from google.genai import types

    model = os.getenv("GEMINI_MODEL", "").strip() or DEFAULT_MODEL
    try:
        client = (client_factory or _default_client_factory)(api_key.strip())
        logger.info("Solicitud a Gemini model=%s stats=%s", model, stats_hash)
        response = client.models.generate_content(
            model=model,
            contents=template.replace("{stats}", aggregated_stats),
            config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=RESPONSE_SCHEMA),
        )
        text = (getattr(response, "text", None) or "").strip()
    except Exception as exc:  # red, timeout, cuota, credenciales, modelo
        message = _classify_error(exc)
        # Solo el tipo y el código: el mensaje de la excepción podría contener datos de la petición.
        logger.warning("Fallo en Gemini (stats=%s): %s code=%s", stats_hash, type(exc).__name__, getattr(exc, "code", "-"))
        return simulated_summary(aggregated_stats, message)

    try:
        summary, findings, recommendations = _parse(text)
    except (ValueError, KeyError, TypeError) as exc:
        logger.warning("Respuesta de Gemini con formato inválido (stats=%s): %s %r", stats_hash, type(exc).__name__, text[:200])
        return simulated_summary(aggregated_stats, MSG_BAD_FORMAT)

    unverified = unverified_numbers(" ".join([summary, *findings, *recommendations]), aggregated_stats)
    warning = MSG_UNVERIFIED.format(numbers=", ".join(unverified)) if unverified else None
    return _result(aggregated_stats, summary, findings, recommendations, simulated=False, warning=warning)


def format_report(result: Dict) -> str:
    """Informe en texto plano (exportación .txt) que separa datos calculados e interpretación."""
    source = "SIMULADA, sin Gemini" if result["simulated"] else "generada por Gemini"
    return (
        f"RESUMEN EJECUTIVO ({source})\n{result['summary']}\n\n"
        f"DATOS CALCULADOS (Python, verificables)\n{result['facts']}\n\n"
        f"HALLAZGOS (interpretación {source})\n{_bullets(result['findings'])}\n\n"
        f"RECOMENDACIONES (interpretación {source})\n{_bullets(result['recommendations'])}\n"
    )


def _bullets(items: List[str]) -> str:
    return "\n".join(f"- {i}" for i in items)


def speech_text(result: Dict) -> str:
    """Texto para narrar: resumen, hallazgos y recomendaciones (sin la tabla de datos)."""
    return " ".join([
        "Resumen ejecutivo.", result["summary"],
        "Hallazgos.", *result["findings"],
        "Recomendaciones.", *result["recommendations"],
    ]).replace("[SIMULADA]", "Simulado:")
