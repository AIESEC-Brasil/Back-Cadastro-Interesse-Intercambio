"""Módulo de integração para criação e sincronização assíncrona de Leads.

Este módulo orquestra o fluxo de cadastro em duas etapas principais:
    1. Registro inicial na plataforma EXPA via Google Apps Script para geração do 'person_id'.
    2. Criação do card do Lead no Podio com o ID do EXPA vinculado e gestão de fallback
       automático de token de acesso expirado.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import logging  # Importação do módulo de logging para registro de diagnósticos
from typing import Any, Dict, Union  # Módulo de tipagem estática

# Importação da função utilitária para desempacotar respostas HTTP
from app.utils import resolve_response

# Importação da classe cliente HTTP customizada
from ..http_request import HttpClient

# Importação das funções utilitárias do Podio
from .podio import buscar_id_card, buscar_token, enviar_comentario

# Importação dos DTOs e tipos de retorno
from app.dto import HttpStatus

# Instancia o logger específico deste módulo
logger = logging.getLogger(__name__)

# Cliente base pré-configurado para a API do Podio
http = HttpClient(base_url="https://api.podio.com", prefix="/item/app")


# =================================================================
# 2. LÓGICA DE NEGÓCIO / INTEGRAÇÃO
# =================================================================

@validar
async def adicionar_lead(
        chave: str,
        payload: Dict[str, Any],
        payload_expa: Dict[str, Any],
        app_id: int,
        response_dto: Dict[str, Any],
) -> tuple[Any, HttpStatus] | tuple[dict[str, str], HttpStatus] | tuple[dict[str, Any], HttpStatus]:
    """Cria a conta do lead no EXPA e insere o card correspondente no Podio.

    Args:
        chave (str): Chave identificadora da configuração de serviço/token no cache.
        payload (Dict[str, Any]): Estrutura de campos e valores no formato esperado pelo Podio.
        payload_expa (Dict[str, Any]): Dicionário com dados do lead formatados para o EXPA.
        app_id (int): Identificador numérico do aplicativo no Podio alvo da criação.
        response_dto (Dict[str, Any]): Dicionário base derivado do DTO de entrada.

    Returns:
        tuple[Any, HttpStatus] | tuple[dict[str, str], HttpStatus] | tuple[dict[str, Any], HttpStatus]:
            Tupla com o payload de resposta e o Enum HttpStatus correspondente.
    """
    # Lazy imports para evitar dependências circulares durante a inicialização dos módulos
    from app.cache import cache  # Cache em memória
    from app.middlewares.registrando_token_rota import CONFIG_MAP, _fetch_token  # Funções de gestão de token
    from app.core import APPSCRIPT_EXPA, TOKEN_EXPA

    logger.info("Iniciando processo de adição e sincronização de Lead (EXPA -> Podio).")

    # Cliente base pré-configurado para a API do AppScript EXPA
    http_expa = HttpClient(base_url=APPSCRIPT_EXPA)

    # === STEP 1: CADASTRO E OBTENÇÃO DE ID NO EXPA ===
    payload_expa["tokenExpa"] = TOKEN_EXPA

    try:
        logger.info("Enviando requisição de cadastro de Lead para a API do EXPA...")
        res_expa = http_expa.post(payload=payload_expa)
        status_expa, data_expa = await resolve_response(res_expa)

        # Valida se a resposta do EXPA permaneceu no intervalo de sucesso (200-399)
        if not data_expa["sucesso"]:
            logger.warning(
                "Falha no retorno do EXPA. Status HTTP: %s. Resposta: %s",
                data_expa.get("status_code"),
                data_expa,
            )
            status_code = data_expa.pop("status_code")
            # Converte o status_code (int) para o Enum HttpStatus
            return data_expa, HttpStatus(status_code)

        # Insere o EP ID do EXPA dentro da estrutura de campos do Podio
        payload["fields"]["di-ep-id-2"] = data_expa.get("person_id","N/A")
        logger.info("Lead cadastrado no EXPA com sucesso!")

    except Exception as err:
        logger.error("Erro inesperado durante comunicação com a API do EXPA: %s", err, exc_info=True)
        return {"erro": str(err)}, HttpStatus.BAD_REQUEST

    # === STEP 2: CADASTRO NO PODIO COM REFRESH AUTOMÁTICO DE TOKEN ===
    logger.info("Iniciando criação do item no Podio (app_id: %s)...", app_id)

    headers = {
        "Authorization": f"Bearer {buscar_token(chave)}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Primeira tentativa de criação do item na API do Podio
    res_podio = http.post(path=f"/{app_id}", payload=payload, headers=headers)
    status, data = await resolve_response(res_podio)

    # Trata erros da faixa 4xx (como 401 Unauthorized), forçando resync do token no cache
    if 400 <= status <= 499 and status != 405:
        logger.warning(
            "Recebido status %s do Podio. Tentando atualizar o token e reexecutar a requisição...",
            status,
        )
        service = "new-lead-ogx"
        config = CONFIG_MAP.get(service)

        if config:
            await cache.get_or_set(
                key=chave,
                fetch=_fetch_token,
                baixando=f"Chave de Acesso ao Podio ({service})",
                resync=True,
            )

            headers["Authorization"] = f"Bearer {buscar_token(chave)}"

            logger.info("Reenviando requisição de criação ao Podio com novo token...")
            res_podio = http.post(path=f"/{app_id}", payload=payload, headers=headers)
            status, data = await resolve_response(res_podio)

    # Garante que a requisição no Podio foi concluída com sucesso
    if not 200 <= status <= 399:
        logger.error("Falha ao adicionar lead no Podio após tentativas. Status: %s. Resposta: %s", status, data)
        # Converte o status (int) para o Enum HttpStatus
        return data, HttpStatus(status)

    logger.info("Item criado no Podio com sucesso (Status: %s).", status)

    # === STEP 3: PREPARAÇÃO E RETORNO DA RESPOSTA FINAL ===
    item_id = buscar_id_card(data)
    logger.info("Extraído item_id do Podio: %s. Finalizando requisição (HTTP 201 CREATED).", item_id)

    response_dto["item_id"] = item_id
    await enviar_comentario(item_id,"Lead se Inscreveu de forma orgânica no Site da Aiesec no Brasil")

    return response_dto, HttpStatus.CREATED


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["adicionar_lead"]