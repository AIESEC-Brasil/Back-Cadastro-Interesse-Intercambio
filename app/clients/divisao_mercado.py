"""Clientes de integração dos metadados de divisão de mercado."""

from typing import Any, Tuple
from app.config import APPSCRIPT_DIVISAO_MERCADO
from .http_request import HttpClient


# ==============================================================================
# CLIENTE DE DIVISÃO DE MERCADO
# ==============================================================================
_http: HttpClient = HttpClient(timeout=60)


def _endpoint(configured_endpoint: str) -> str:
    """Aceita a URL publicada ou o ID de implantação do Apps Script."""
    endpoint: str = configured_endpoint.strip()
    if endpoint.startswith(("https://", "http://")):
        return endpoint
    return f"https://script.google.com/macros/s/{endpoint}/exec"


async def _enviar_metadados(recurso: str) -> Tuple[int, Any]:
    """Consulta um recurso da divisão de mercado no Apps Script."""
    return await _http.get(
        path=_endpoint(APPSCRIPT_DIVISAO_MERCADO),
        params={"recurso": recurso},
    )


async def enviar_metadados_escritorios() -> Tuple[int, Any]:
    """Consulta os metadados de escritórios no Apps Script configurado."""
    return await _enviar_metadados("escritorios")


async def enviar_metadados_universidades() -> Tuple[int, Any]:
    """Consulta os metadados de universidades no Apps Script configurado."""
    return await _enviar_metadados("universidades")


__all__ = ["enviar_metadados_escritorios", "enviar_metadados_universidades"]
