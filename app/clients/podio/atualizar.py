from typing import Any,Tuple
from .podio import buscar_token,buscar_id_card
from ..http_request import HttpClient
from app.utils import resolve_response

# Cliente base para autenticação e chamadas gerais
http = HttpClient(base_url="https://api.podio.com",prefix="/item")

@validar
async def atualizar_lead(chave: str, payload: Any, data_response: dict) -> dict:
    """
    Atualiza dados de um card existente.
    Usa o 'item_id' (ID global do Podio) extraído de uma criação anterior.
    """
    item_id = buscar_id_card(data_response)
    """headers = {
        "Authorization": f"Bearer {buscar_token(chave)}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    # Método PUT para substituição/atualização dos campos enviados
    response = http.put(path=f"/{item_id}", payload=payload, headers=headers)
    status, data = await resolve_response(response)"""
    payload["item_id"] = item_id
    return payload

__all__ = ["atualizar_lead"]