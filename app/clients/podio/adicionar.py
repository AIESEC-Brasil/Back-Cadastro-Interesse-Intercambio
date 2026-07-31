from typing import Any
from .podio import buscar_token
from ..http_request import HttpClient
from app.utils import resolve_response

# Cliente base para autenticação e chamadas gerais
http = HttpClient(base_url="https://api.podio.com",prefix="/item/app")

@validar
async def adicionar_lead(chave: str, data: Any, APP_ID: int) -> tuple[dict, int]:
    """
    Cria um card no Podio.
    Retorna o corpo da resposta e o 'app_item_id' (ID sequencial amigável).
    """
    headers = {
        "Authorization": f"Bearer {buscar_token(chave)}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    # Payload deve ser um dicionário com a chave "fields" (conforme DTO de Output)
    response = http.post(path=f"/{APP_ID}", payload=data, headers=headers)
    status, data = await resolve_response(response)

    return data

__all__ = ["adicionar_lead"]