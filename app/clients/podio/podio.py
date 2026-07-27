"""
Cliente de integração com a API do Podio.

Provê funções para autenticação via credenciais de App, além de operações
básicas de CRUD de itens (cards) relacionados ao app do Podio.
"""

# ==============================
# Importações (Dependencies)
# ==============================
from typing import Any, Dict, Tuple        # Tipagem estática
from ..http_request import HttpClient # Cliente base assíncrono
from app.utils import agora                     # Captura timestamp atual (Brasil)
from app.utils import resolve_response          # Utilitário para tratar Coroutines/Respostas HTTP
from app.cache import cache                     # Sistema de armazenamento temporário de tokens

# =================================================================
# INSTÂNCIAS DE CLIENTES (Contextos do Podio)
# =================================================================

#

# Cliente base para autenticação e chamadas gerais
http = HttpClient(base_url="https://api.podio.com")

# =================================================================
# FUNÇÕES DE AUTENTICAÇÃO
# =================================================================

@validar
async def getAcessToken(item: str | Dict[str, Any], PATH: str = "/oauth/token") -> tuple[int, dict[str, Any]]:
    """
    Obtém tokens de acesso/refresh do Podio usando o fluxo 'App Authentication'.

    Args:
        item: Dicionário com CLIENT_ID, CLIENT_SECRET, APP_ID e APP_TOKEN.
        PATH: Endpoint de autenticação.

    Returns:
        Status HTTP e payload contendo tokens e metadados de expiração.
    """
    # Montagem do formulário de autenticação exigido pelo Podio (x-www-form-urlencoded)
    payload = {
        "grant_type": "app",
        "client_id": item["CLIENT_ID"],
        "client_secret": item["CLIENT_SECRET"],
        "app_id": item["APP_ID"],
        "app_token": item["APP_TOKEN"]
    }
    try:
        # Realiza a requisição POST assíncrona
        respose = http.post(path=PATH, payload=payload, as_form=True)

        # Resolve a resposta (trata await e extrai dados)
        status, data = await resolve_response(respose)

        # 🛑 Tratamento de Erro Crítico: Se as credenciais estiverem erradas, para o processo.
        if status != 200:
            error_msg = data.get("error_description", "Erro desconhecido no Podio")
            raise ValueError(f"Parada Crítica: Falha na Autenticação ({status}) - {error_msg}")

        # ✨ Retorno formatado para ser armazenado na estrutura de Cache da aplicação
        return status, {
            "access_token": data["access_token"],
            "expires_in": data["expires_in"],
            "refresh_token": data["refresh_token"],
            "created_at": agora() # Timestamp para controle de expiração manual se necessário
        }

    except KeyError as e:
        raise RuntimeError(f"Erro de estrutura nos dados do Podio: Chave {e} não encontrada.") from e
    except Exception as e:
        raise RuntimeError(f"Erro Fatal na integração: {str(e)}") from e

@validar
def buscarToken(chave: str) -> str:
    """
    Recupera o access_token válido de dentro do dicionário de Cache.
    A chave geralmente é o nome do Workspace (ex: 'OGX').
    """
    return cache.store[chave]["data"]["access_token"]

# =================================================================
# OPERAÇÕES DE APP E LEADS
# =================================================================

@validar
async def metadados(chave: str, APP_ID: int) -> Tuple[int, dict]:
    """Busca informações estruturais de um App (campos, slugs, tipos)."""
    headers = {
        "Authorization": f"Bearer {buscarToken(chave)}", # Autenticação via Token no Header
        "Content-Type": "application/json"
    }
    response = http.get(path=f"/app/{APP_ID}", headers=headers)
    status, data = await resolve_response(response)
    return status, data

# =================================================================
# UTILITÁRIOS DE EXTRAÇÃO DE IDs
# =================================================================

@validar
def buscar_id_card(data: dict) -> Any | None:
    """Extrai o 'item_id' (ID único e imutável no banco de dados do Podio)."""
    return data.get("item_id")

# ==============================
# Exportações do Módulo
# ==============================
__all__ = [
    "getAcessToken",
    "buscarToken",
    "metadados",
    "buscar_id_card"
]