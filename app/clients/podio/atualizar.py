"""
Módulo de Integração com a API do Podio para Atualização de Leads.

Este módulo disponibiliza a função `atualizar_lead`, responsável por realizar
a requisição HTTP PUT para alteração de dados de um card existente no Podio,
contando com mecanismo automático de renovação de token no cache (fallback 4xx).
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================

import logging  # Módulo para registro de diagnósticos e logs
from typing import Any, Dict  # Módulo de tipagem estática

# Importação da função utilitária para desempacotar e resolver respostas HTTP
from app.utils import resolve_response

# Importação dos DTOs e tipos de retorno
from app.dto import HttpStatus

# Importação do cliente HTTP genérico
from ..http_request import HttpClient

# Importação das funções utilitárias do Podio
from .podio import buscar_id_card, buscar_token, enviar_comentario

# Instancia o logger específico deste módulo
logger = logging.getLogger(__name__)


# =================================================================
# 2. CLIENTE HTTP E CONFIGURAÇÕES GLOBAIS
# =================================================================

# Cliente base pré-configurado para chamadas de alteração de itens no Podio
http = HttpClient(base_url="https://api.podio.com", prefix="/item")


# =================================================================
# 3. FUNÇÃO DE ATUALIZAÇÃO DE DADOS (LEAD)
# =================================================================

# @validar  # Descomente o decorador conforme a necessidade da sua aplicação
async def atualizar_lead(
        chave: str,
        payload: Dict[str, Any],
        response_dto: Dict[str, Any],
        data_response: Dict[str, Any],
        service: str = "new-lead-ogx",
        atualizar:str = "registro"
) -> tuple[Any, HttpStatus] | dict[str, Any]:
    """
    Atualiza os dados de um card (Lead) existente na plataforma do Podio.

    Extrai o `item_id` (ID global do Podio) da resposta de criação prévia e dispara
    uma requisição HTTP PUT. Caso receba um erro da faixa 4xx (como 401 Unauthorized),
    força a renovação do token no cache e reexecuta a chamada.

    Args:
        chave (str): Chave identificadora do serviço/token armazenado no cache.
        payload (Dict[str, Any]): Dicionário com os campos a serem atualizados no Podio.
        response_dto (Dict[str, Any]): Dicionário base derivado do DTO de entrada.
        data_response (Dict[str, Any]): Dicionário com a resposta da criação prévia contendo o `item_id`.
        service (str, optional): Nome do serviço mapeado no CONFIG_MAP para renovação do token. Padrão: "new-lead-ogx".
        atualizar(str): Tipo de atualização se é um lead se reescrevendo ou é da pagina de qualificação

    Returns:
        Dict[str, Any]: O payload atualizado e enriquecido com o 'item_id'.

    Raises:
        ValueError: Caso a API do Podio retorne status diferente de 204 após o retry.
        KeyError: Se o 'item_id' não for encontrado dentro de `data_response`.
    """
    # Importações tardias (lazy imports) para evitar dependências circulares
    from app.cache import cache  # Cache em memória
    from app.middlewares.registrando_token_rota import CONFIG_MAP, _fetch_token  # Gestão de tokens

    # Extrai o ID global do item no Podio a partir da resposta anterior
    item_id = buscar_id_card(data_response)

    logger.info("Iniciando atualização do item no Podio...")

    # Monta os cabeçalhos HTTP necessários para autenticação na API do Podio
    headers = {
        "Authorization": f"Bearer {buscar_token(chave)}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Primeira tentativa de atualização do item no Podio
    res_podio = http.put(path=f"/{item_id}", payload=payload, headers=headers)
    status, data = await resolve_response(res_podio)

    # === REFRESH AUTOMÁTICO DE TOKEN SE HOUVER ERRO NA FAIXA 4XX ===
    if 400 <= status <= 499 and status != 405:
        logger.warning(
            "Recebido status %s do Podio ao atualizar item. Tentando renovar o token...",
            status,
        )
        config = CONFIG_MAP.get(service)

        if config:
            # Força a re-busca (resync=True) do token e atualiza a chave no cache
            await cache.get_or_set(
                key=chave,
                fetch=_fetch_token,
                baixando=f"Chave de Acesso ao Podio ({service})",
                resync=True,
            )

            # Atualiza o cabeçalho Authorization com o novo token obtido do cache
            headers["Authorization"] = f"Bearer {buscar_token(chave)}"

            logger.info("Reenviando requisição de atualização ao Podio com o novo token...")
            res_podio = http.put(path=f"/{item_id}", payload=payload, headers=headers)
            status, data = await resolve_response(res_podio)

    # Garante que a requisição no Podio foi concluída com sucesso
    if not 200 <= status <= 399:
        logger.error("Falha ao atualizar lead no Podio após tentativas. Status: %s. Resposta: %s", status, data)
        # Converte o status (int) para o Enum HttpStatus
        return data, HttpStatus(status)

    logger.info("Item atualizado com sucesso no Podio.")

    # Anexa o item_id ao payload para rastreabilidade e retorno
    response_dto["item_id"] = item_id
    if atualizar == 'registro':
        await enviar_comentario(item_id, "Lead se reinscreveu no Site da Aiesec no Brasil")
    elif atualizar == 'qualificação' and any(not valor for chave,valor in data_response.items() if chave != 'item_id'):
        await enviar_comentario(item_id, "Lead preencheu as qualificações")
    return response_dto, HttpStatus.OK


# =================================================================
# 4. EXPORTAÇÃO CONSOLIDADA DO MÓDULO
# =================================================================

__all__ = ["atualizar_lead"]