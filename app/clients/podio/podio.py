"""Módulo de Integração com a API do Podio.

Provê funções para autenticação via credenciais de aplicativo (App Authentication)
e operações essenciais de metadados e manipulação de itens/cards do Podio.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from typing import Any, Dict, Tuple  # Anotação formal de tipos estáticos
from datetime import datetime, timedelta # Módulo nativo para manipulação e cálculos de datas e horários
from app.cache import cache  # Sistema de cache em memória para armazenar tokens
from app.utils import agora  # Helper para captura de timestamp atual
from app.utils import resolve_response  # Resolver assíncrono de respostas HTTP
from app.dto import HttpStatus # modulo enum para status http
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
    """Obtém ou renova tokens do Podio apenas se necessário ou forçado.

    Args:
        item (Dict[str, Any]): Dicionário contendo credenciais e tokens.
        path (str, optional): Endpoint de autenticação OAuth2.

    Returns:
        Tuple[int, Dict[str, Any]]: Status HTTP e dados do token atualizado ou em cache.
    """
    """
    # 1. Recupera valores em cache aceitando tipos string/None para evitar avisos do linter
    created_at_raw: str | None = item.get("CREATED_AT")
    raw_expires_in: int | timedelta | None = item.get("EXPIRES_IN")
    access_token: str | None = item.get("ACCESS_TOKEN")

    # 2. Valida se o token em cache ainda está dentro do período de validade
    if created_at_raw and raw_expires_in and access_token:
        # Converte a string armazenada para um objeto datetime para permitir operações matemáticas
        created_at = datetime.fromisoformat(created_at_raw)

        # Garante que expires_in seja um objeto timedelta (mesmo que venha como int do Podio/Cache)
        expires_in = (
            raw_expires_in
            if isinstance(raw_expires_in, timedelta)
            else timedelta(seconds=int(raw_expires_in))
        )

        # Converte a margem de segurança (60 segundos) para um objeto timedelta
        margem_seguranca = timedelta(seconds=60)

        # Calcula o tempo decorrido entre a criação e o momento atual
        tempo_decorrido = agora() - created_at
        # Compara se o tempo decorrido é menor que o limite de expiração (com margem de segurança)
        if tempo_decorrido < (expires_in - margem_seguranca):
            return HttpStatus.OK, {
                "access_token": access_token,
                "expires_in": expires_in,
                "refresh_token": item.get("REFRESH_TOKEN"),
                "created_at": created_at_raw,
            }"""

    # 3. Prepara o payload caso o token precise ser gerado/renovado no Podio
    if item.get("REFRESH_TOKEN"):
        # Prioridade: renova via refresh_token
        payload = {
            "grant_type": "refresh_token",
            "client_id": item["CLIENT_ID"],
            "client_secret": item["CLIENT_SECRET"],
            "refresh_token": item["REFRESH_TOKEN"],
        }
    else:
        # Fallback: autentica via app (primeira autenticação)
        payload = {
            "grant_type": "app",
            "client_id": item["CLIENT_ID"],
            "client_secret": item["CLIENT_SECRET"],
            "app_id": item["APP_ID"],
            "app_token": item["APP_TOKEN"],
        }

    try:
        # Dispara a requisição POST assíncrona para a API do Podio
        response = http.post(path=path, payload=payload, as_form=True)
        status, data = await resolve_response(response)
        # Trata possíveis erros retornados pelo Podio
        if status != HttpStatus.OK:
            msg_erro = data.get(
                "error_description", "Erro desconhecido no Podio."
            )
            raise ValueError(
                f"Parada Crítica: Falha na Autenticação ({status}) - {msg_erro}"
            )

        # Retorna o novo token recebido e atualiza a data de criação
        return status, {
            "access_token": data["access_token"],
            "expires_in": int(data["expires_in"]),
            "refresh_token": data["refresh_token"],  # Novo refresh token gerado
            "created_at": agora().isoformat(),      # Salva como string ISO para persistência
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