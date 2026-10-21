"""Cliente de integração com o Apps Script EXPA."""

from typing import Any, Tuple

from app.config import APPSCRIPT_EXPA
from app.dto import PayloadExpa
from .http_request import HttpClient


_http: HttpClient = HttpClient(timeout=60)


def _endpoint() -> str:
    """Aceita tanto a URL publicada quanto o ID de implantação do script."""
    endpoint: str = APPSCRIPT_EXPA.strip()
    if endpoint.startswith(("https://", "http://")):
        return endpoint
    return f"https://script.google.com/macros/s/{endpoint}/exec"


async def enviar_payload_expa(payload: PayloadExpa) -> Tuple[int, Any]:
    """Envia ao Apps Script o DTO serializado com os campos esperados pelo GAS."""
    return await _http.post(
        path=_endpoint(),
        payload=payload.model_dump(mode="json", by_alias=True),
    )


__all__ = ["enviar_payload_expa"]
