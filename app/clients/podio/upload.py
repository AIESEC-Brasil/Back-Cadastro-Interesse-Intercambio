"""
Módulo de Integração com a API do Podio para Envio e Anexo de Arquivos.

Este módulo disponibiliza a função `upload_e_anexar_curriculo`, responsável por realizar
as requisições HTTP POST para upload de arquivos e vínculo com cards existentes no Podio,
contando com mecanismo automático de renovação de token no cache (fallback 4xx).
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================

import base64  # Módulo nativo para codificação e conversão de dados em Base64
import logging  # Módulo para registro de diagnósticos e logs
from typing import Any, Dict  # Módulo de tipagem estática

# Importação da função utilitária para desempacotar e resolver respostas HTTP
from app.utils import resolve_response

# Importação dos DTOs e tipos de retorno
from app.dto import HttpStatus, QualificacaoLead

# Importação dos formatadores de payload de anexo
from app.helper import payload_anexar_arquivo_podio

# Importação do cliente HTTP genérico
from ..http_request import HttpClient

# Importação das funções utilitárias do Podio
from .podio import buscar_token

# Instancia o logger específico deste módulo
logger = logging.getLogger(__name__)


# =================================================================
# 2. CLIENTE HTTP E CONFIGURAÇÕES GLOBAIS
# =================================================================

# Cliente base pré-configurado para chamadas do recurso de arquivos no Podio
http = HttpClient(base_url="https://api.podio.com", prefix="/file")


# =================================================================
# 3. FUNÇÃO DE UPLOAD E ANEXO DE ARQUIVO (CURRÍCULO)
# =================================================================

# @validar  # Descomente o decorador conforme a necessidade da sua aplicação
async def upload_e_anexar_curriculo(
        chave: str,
        data: QualificacaoLead,
        response_dto: Dict[str, Any],
        service: str = "new-lead-ogx",
) -> tuple[Any, HttpStatus] | dict[str, Any]:
    """
    Realiza o upload do currículo para a API do Podio e o anexa ao card (Lead) correspondente.

    Valida a presença do arquivo no DTO, executa o upload via multipart/form-data e em seguida
    anexa o arquivo gerado ao `item_id`. Caso receba um erro da faixa 4xx (como 401 Unauthorized)
    em qualquer uma das chamadas, força a renovação do token no cache e reexecuta a operação.

    Args:
        chave (str): Chave identificadora do serviço/token armazenado no cache.
        data (QualificacaoLead): Objeto DTO contendo as informações do lead e o arquivo do currículo.
        response_dto (Dict[str, Any]): Dicionário base derivado do DTO de entrada.
        service (str, optional): Nome do serviço mapeado no CONFIG_MAP para renovação do token. Padrão: "new-lead-ogx".

    Returns:
        tuple[Any, HttpStatus] | dict[str, Any]: Estrutura com a resposta e o status HTTP.
    """
    # Importações tardias (lazy imports) para evitar dependências circulares
    from app.cache import cache  # Cache em memória
    from app.middlewares.registrando_token_rota import CONFIG_MAP, _fetch_token  # Gestão de tokens

    # Validação defensiva: garante a existência do objeto de currículo antes do envio
    if not data.curriculo:
        logger.warning("Tentativa de upload cancelada: arquivo de currículo não fornecido no DTO.")
        return {"mensagem": "Arquivo de currículo não fornecido."}, HttpStatus.BAD_REQUEST

    logger.info("Iniciando processo de upload do currículo para o Podio...")

    # =================================================================
    # ETAPA 1: UPLOAD DO ARQUIVO (POST https://api.podio.com/file/)
    # =================================================================

    # Monta os cabeçalhos HTTP com o Bearer Token obtido do cache
    headers_upload = {
        "Authorization": f"Bearer {buscar_token(chave)}",
        "Accept": "application/json",
    }

    # Prepara o arquivo binário para transmissão Multipart/Form-Data (chave 'source')
    file_param = {"source": (data.curriculo.nome, data.curriculo.base64, "application/pdf")}

    # Campo de texto obrigatório para a API do Podio associar o nome original
    data_param = {"filename": data.curriculo.nome}

    # Dispara a requisição HTTP POST de upload
    res_upload = http.post(path="", files=file_param, payload=data_param, headers=headers_upload)
    status, data_res = await resolve_response(res_upload)

    # === REFRESH AUTOMÁTICO DE TOKEN SE HOUVER ERRO NA FAIXA 4XX (UPLOAD) ===
    if 400 <= status <= 499 and status != 405:
        logger.warning(
            "Recebido status %s do Podio ao realizar upload do arquivo. Tentando renovar o token...",
            status,
        )
        config = CONFIG_MAP.get(service)

        if config:
            # Força a renovação síncrona da credencial no cache
            await cache.get_or_set(
                key=chave,
                fetch=_fetch_token,
                baixando=f"Chave de Acesso ao Podio ({service})",
                resync=True,
            )

            # Atualiza os cabeçalhos com o novo token renovado
            headers_upload["Authorization"] = f"Bearer {buscar_token(chave)}"

            logger.info("Reenviando requisição de upload ao Podio com o novo token...")
            res_upload = http.post(path="", files=file_param, payload=data_param, headers=headers_upload)
            status, data_res = await resolve_response(res_upload)

    # Aborta o fluxo caso o upload falhe permanentemente
    if not 200 <= status <= 399:
        logger.error("Falha ao realizar upload do arquivo no Podio. Status: %s. Resposta: %s", status, data_res)
        return data_res, HttpStatus(status)

    # Extrai o identificador único gerado para o arquivo recém-criado
    file_id = data_res.get("file_id")
    logger.info("Upload realizado com sucesso no Podio.")

    # =================================================================
    # ETAPA 2: ANEXAR ARQUIVO AO ITEM (POST https://api.podio.com/file/{file_id}/attach)
    # =================================================================
    # Monta o payload JSON contendo a referência da entidade alvo ({ref_type: 'item', ref_id: item_id})
    attach_payload = payload_anexar_arquivo_podio(data)

    headers_attach = {
        "Authorization": f"Bearer {buscar_token(chave)}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    logger.info("Anexando arquivo ao item do Podio...")

    # Dispara a requisição HTTP POST para associar o arquivo ao item
    res_attach = http.post(path=f"/{file_id}/attach", payload=attach_payload, headers=headers_attach)
    status, data_res = await resolve_response(res_attach)

    # === REFRESH AUTOMÁTICO DE TOKEN SE HOUVER ERRO NA FAIXA 4XX (ATTACH) ===
    if 400 <= status <= 499 and status != 405:
        logger.warning(
            "Recebido status %s do Podio ao anexar arquivo ao item. Tentando renovar o token...",
            status,
        )
        config = CONFIG_MAP.get(service)

        if config:
            # Força a renovação síncrona da credencial no cache
            await cache.get_or_set(
                key=chave,
                fetch=_fetch_token,
                baixando=f"Chave de Acesso ao Podio ({service})",
                resync=True,
            )

            # Atualiza os cabeçalhos com o novo token renovado
            headers_attach["Authorization"] = f"Bearer {buscar_token(chave)}"

            logger.info("Reenviando requisição de anexo ao Podio com o novo token...")
            res_attach = http.post(path=f"/{file_id}/attach", payload=attach_payload, headers=headers_attach)
            status, data_res = await resolve_response(res_attach)

    # Aborta o fluxo caso o anexo falhe permanentemente
    if not 200 <= status <= 399:
        logger.error("Falha ao anexar arquivo ao item no Podio. Status: %s. Resposta: %s", status, data_res)
        return data_res, HttpStatus(status)

    logger.info("Arquivo anexado com sucesso ao item no Podio.")

    # Deleta a chave do currículo com os bytes do objeto de resposta para evitar erro no jsonify
    if data.curriculo: del response_dto["curriculo"]
    response_dto["item_id"] = data.item_id
    return response_dto, HttpStatus.OK


# =================================================================
# 4. EXPORTAÇÃO CONSOLIDADA DO MÓDULO
# =================================================================

__all__ = ["upload_e_anexar_curriculo"]