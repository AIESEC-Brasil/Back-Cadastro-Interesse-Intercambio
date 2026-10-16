"""Cliente de integração com o Apps Script B2C."""

from typing import Any, Tuple

from app.config import APPSCRIPT_B2C
from .http_request import HttpClient


_http = HttpClient(timeout=60)


def _endpoint() -> str:
    """Aceita tanto a URL publicada quanto o ID de implantação do script."""
    endpoint = APPSCRIPT_B2C.strip()
    if endpoint.startswith(("https://", "http://")):
        return endpoint
    return f"https://script.google.com/macros/s/{endpoint}/exec"


async def enviar_metadados_b2c() -> Tuple[int, Any]:
    """Consulta os metadados B2C no Apps Script configurado."""
    return await _http.get(path=_endpoint())


__all__ = ["enviar_metadados_b2c"]
