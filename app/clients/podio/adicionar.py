# Importação de tipo de anotação de tipo genérico do Python
from types import CoroutineType
from typing import Any

# Importação das funções utilitárias para manipular dados específicos do Podio (extrair ID e buscar token)
from .podio import buscar_id_card, buscar_token

# Importação da classe cliente HTTP customizada para realizar requisições assíncronas
from ..http_request import HttpClient

# Importação da função utilitária para desempacotar e formatar as respostas das requisições HTTP
from app.utils import resolve_response

# Cliente base pré-configurado com a URL base do Podio e o prefixo da rota de aplicativos
http = HttpClient(base_url="https://api.podio.com", prefix="/item/app")


@validar
async def adicionar_lead(chave: str, payload: Any, app_id: int, response_dto: Any) -> CoroutineType[
    Any, Any, tuple[int, Any]]:
    """Cria um card de lead no Podio.

    Dispara a requisição de inserção para o Podio utilizando o token em cache.
    Caso o Podio retorne erro de autenticação (401 Unauthorized), força o resync
    do cache para obter um token válido e realiza uma segunda tentativa.

    Args:
        chave (str): Chave identificadora do serviço/configuração (ex: 'new-lead-ogx').
        payload (Any): Dicionário contendo os dados do formulário/lead a ser criado.
        app_id (int): ID do aplicativo no Podio onde o item será inserido.
        response_dto (Any) : Payload do dto usado para transferencia

    Returns:
        tuple[dict, int]: Tupla contendo o payload atualizado (com 'item_id') e o status HTTP.
    """
    # Importação do gerenciador de cache centralizado da aplicação (lazy import para evitar importação circular)
    from app.cache import cache

    # Importação do mapa de configurações dos serviços e da função fetch de token (lazy import)
    from app.middlewares.registrando_token_rota import CONFIG_MAP, _fetch_token

    # Prepara os cabeçalhos padrão da requisição com o token atual recuperado do cache
    headers = {
        "Authorization": f"Bearer {buscar_token(chave)}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # === PRIMEIRA TENTATIVA ===
    # Envia o payload para a API do Podio no app específico
    response = http.post(path=f"/{app_id}", payload=payload, headers=headers)
    status, data = await resolve_response(response)

    # === FALLBACK: TRATAMENTO PARA TOKEN EXPIRADO (STATUS 4xx) ===
    # Intercepta falha de autenticação caso o token tenha vencido no limite da requisição
    if 400 <= status <= 499 and  status != 405:
        # Recupera as configurações do serviço através da chave informada
        service="new-lead-ogx"
        config = CONFIG_MAP.get(service)

        if config:
            # Força a busca de um novo token diretamente na API do Podio (resync=True)
            await cache.get_or_set(
                key=chave,
                fetch=_fetch_token,
                baixando=f"Chave de Acesso ao Podio ({service})",
                resync=True,   # Bypassa o token expirado existente no cache
            )

            # Atualiza o cabeçalho Authorization com a nova credencial gerada
            headers["Authorization"] = f"Bearer {buscar_token(chave)}"

            # Re-executa a requisição de inserção com o novo token
            response = http.post(path=f"/{app_id}", payload=payload, headers=headers)
            status, data = await resolve_response(response)

    # Lança erro se permanecer falhando (ou se for erro 400, 404, 500, etc)
    if  not 200 <= status <= 399:
        raise ValueError(f"Falha ao adicionar lead no Podio ({status}): {data}")

    # Associa o ID do card gerado/retornado pelo Podio ao dicionário do payload
    response_dto["item_id"] = buscar_id_card(data)
    # Retorna o payload processado e o status final da resposta HTTP
    return response_dto


__all__ = ["adicionar_lead"]