"""Módulo de Integração com a API do Podio.

Provê funções para autenticação via credenciais de aplicativo (App Authentication)
e operações essenciais de metadados e manipulação de itens/cards do Podio.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from typing import Any, Dict, Tuple  # Anotação formal de tipos estáticos

from app.cache import cache  # Sistema de cache em memória para armazenar tokens
from app.utils import agora  # Helper para captura de timestamp atual
from app.utils import resolve_response  # Resolver assíncrono de respostas HTTP

from ..http_request import HttpClient  # Instância do cliente HTTP assíncrono base

# =================================================================
# 2. INSTÂNCIAS DE CLIENTES
# =================================================================

# Cliente HTTP dedicado para a API do Podio
http = HttpClient(base_url="https://api.podio.com")


# =================================================================
# 3. FUNÇÕES DE AUTENTICAÇÃO
# =================================================================

async def get_access_token(
        item: Dict[str, Any],
        path: str = "/oauth/token",
) -> Tuple[int, Dict[str, Any]]:
    """Obtém tokens de acesso e refresh do Podio via 'App Authentication'.

    Args:
        item (Dict[str, Any]): Dicionário contendo CLIENT_ID, CLIENT_SECRET,
            APP_ID e APP_TOKEN.
        path (str, optional): Endpoint de autenticação OAuth2.

    Returns:
        Tuple[int, Dict[str, Any]]: Status HTTP e payload com access_token,
            refresh_token e tempo de expiração.

    Raises:
        ValueError: Se as credenciais forem inválidas ou recusadas.
        RuntimeError: Se ocorrer falha na estrutura dos dados ou no envio.
    """
    # Monta o payload no formato x-www-form-urlencoded exigido pelo Podio
    payload = {
        "grant_type": "app",
        "client_id": item["CLIENT_ID"],
        "client_secret": item["CLIENT_SECRET"],
        "app_id": item["APP_ID"],
        "app_token": item["APP_TOKEN"],
    }

    try:
        # Dispara a requisição POST assíncrona
        response = http.post(path=path, payload=payload, as_form=True)

        # Resolve a coroutine e obtém o tuple (status, data)
        status, data = await resolve_response(response)

        # Trata falhas de autenticação (credenciais incorretas ou inválidas)
        if status != 200:
            msg_erro = data.get(
                "error_description", "Erro desconhecido no Podio."
            )
            raise ValueError(
                f"Parada Crítica: Falha na Autenticação ({status}) - {msg_erro}"
            )

        # Estrutura tratada para armazenamento no Cache do sistema
        return status, {
            "access_token": data["access_token"],
            "expires_in": data["expires_in"],
            "refresh_token": data["refresh_token"],
            "created_at": agora(),  # Timestamp local para auditoria
        }

    except KeyError as e:
        raise RuntimeError(
            f"Erro de estrutura nos dados do Podio: Chave {e} não encontrada."
        ) from e
    except Exception as e:
        raise RuntimeError(f"Erro Fatal na integração: {str(e)}") from e


def buscar_token(chave: str) -> str:
    """Recupera o access_token ativo armazenado no dicionário de Cache.

    Args:
        chave (str): Identificador do workspace ou contexto (ex: 'OGX').

    Returns:
        str: Access token válido para requisições na API do Podio.
    """
    return cache.store[chave]["data"]["access_token"]


# =================================================================
# 4. OPERAÇÕES DE APLICATIVOS E METADADOS
# =================================================================

async def metadados(chave: str, app_id: int) -> Tuple[int, Dict[str, Any]]:
    """Recupera a estrutura detalhada de um App no Podio (campos, slugs e tipos).

    Args:
        chave (str): Chave para recuperar o token no cache.
        app_id (int): ID numérico do aplicativo no Podio.

    Returns:
        Tuple[int, Dict[str, Any]]: Status HTTP e dicionário com metadados do App.
    """
    headers = {
        "Authorization": f"Bearer {buscar_token(chave)}",
        "Content-Type": "application/json",
    }
    response = http.get(path=f"/app/{app_id}", headers=headers)
    status, data = await resolve_response(response)
    return status, data


# =================================================================
# 5. UTILITÁRIOS DE EXTRAÇÃO DE DADOS
# =================================================================

def buscar_id_card(data: Dict[str, Any]) -> Any:
    """Extrai o 'item_id' único e imutável de um payload de card/item do Podio.

    Args:
        data (Dict[str, Any]): Dicionário com os dados do card retornado.

    Returns:
        Any: ID do item ou None caso a chave não exista.
    """
    return data.get("item_id")


# =================================================================
# 6. EXPORTAÇÃO PÚBLICA (INTERFACE DO MÓDULO)
# =================================================================

__all__ = [
    "get_access_token",  # Obtém access token via App Authentication
    "buscar_token",  # Recupera o token atrelado à chave no cache
    "metadados",  # Obtém a estrutura e campos de um aplicativo
    "buscar_id_card",  # Extrai o ID único de um item/card
]