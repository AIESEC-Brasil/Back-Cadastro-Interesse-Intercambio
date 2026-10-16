"""Endpoint de metadados do formulário B2C."""

import logging

from asgiref.sync import async_to_sync

from ..cache import cache
from ..clients.b2c import enviar_metadados_b2c
from ..dto.output.metadadosDTO import Metadados
from ..router import Router

new_lead_ogx = Router(name="metadados_b2c", url_prefix="/new-lead-ogx")
logger = logging.getLogger(__name__)


@new_lead_ogx.get(
    "/metadados",
    responses={200: Metadados},
)
def buscar_metadados():
    """
    Busca e retorna os metadados dos campos do formulário B2C.

    A rota consulta o Apps Script B2C e armazena a resposta em cache pelo
    período definido em ``CACHE_TTL``. Opções inativas são removidas antes
    de a resposta ser enviada.

    Estrutura da resposta:
        ``data.fields`` é uma lista de campos. Cada campo contém:

        - ``external_id``: identificador do campo;
        - ``config.settings.description``: descrição, quando definida;
        - ``config.settings.options``: opções ativas disponíveis para o campo.

    Returns:
        dict: Metadados no formato ``{"data": {"fields": [...]}}``.
    """
    logger.info("Requisição recebida para buscar metadados B2C")
    payload, status = async_to_sync(cache.get_or_set)(
        key="metadados_b2c",
        fetch=enviar_metadados_b2c,
    )
    if status < 200 or status >= 300:
        logger.error("Falha ao buscar metadados B2C; status HTTP %s", status)
    else:
        logger.info("Metadados B2C retornados com sucesso")
    metadata = Metadados.model_validate(payload).model_dump()
    return metadata, status


__all__ = ["new_lead_ogx"]
