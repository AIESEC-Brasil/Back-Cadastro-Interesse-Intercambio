from typing import Any,Tuple
from .podio import buscarToken,buscar_id_card
from ..http_request import HttpClient
from app.utils import resolve_response

# Cliente base para autenticação e chamadas gerais
http = HttpClient(base_url="https://api.podio.com",prefix="/item")

@validar
async def remover_lead(chave: str, data_response: dict) -> bool | tuple[bool, Any]:
    """Remove permanentemente um card do CRM."""
    item_id = buscar_id_card(data_response)
    headers = {
        "Authorization": f"Bearer {buscarToken(chave)}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    response = http.delete(path=f"/{item_id}", headers=headers)
    status, data = await resolve_response(response)

    # Status 204 indica que a deleção foi processada com sucesso e não há conteúdo a retornar.
    if status == 204:
        return True
    return False, data

__all__ = ["remover_lead"]