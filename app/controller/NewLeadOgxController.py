"""Endpoint de metadados do formulário B2C."""

import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from asgiref.sync import async_to_sync
from flask_openapi3 import Tag

from ..cache import cache
from ..clients.b2c import enviar_metadados_b2c
from ..dto import HttpStatus, ValidationErrorResponse
from ..dto.output.metadadosDTO import Metadados
from ..router import Router

new_lead_ogx: Router = Router(name="metadados_b2c", url_prefix="/new-lead-ogx")
logger: logging.Logger = logging.getLogger(__name__)

# ==============================================================================
# DOCUMENTAÇÃO DA ROTA DE METADADOS
# ==============================================================================
METADADOS_DESCRIPTION: str = """\
Usa o cache válido ou consulta a origem \
quando ele está ausente ou expirado. Preserva todos os campos do Apps Script \
e remove opções explicitamente inativas.

A resposta contém `data.fields`, com os campos do formulário B2C, e \
`timestamp`, com a última atualização do cache no fuso de São Paulo."""

METADADOS_RESPONSES: dict[int | str, Any] = {
    200: Metadados,
    422: ValidationErrorResponse,
    502: {
        "description": "A origem falhou ou devolveu um payload inválido.",
        "content": {"text/html": {"schema": {"type": "string"}}},
    },
    504: {
        "description": "A consulta à origem excedeu o tempo limite.",
        "content": {"text/html": {"schema": {"type": "string"}}},
    },
    "default": {
        "description": "Outros erros HTTP são exibidos na página genérica de erro.",
        "content": {"text/html": {"schema": {"type": "string"}}},
    },
}

# ==============================================================================
# ROTA DE CONSULTA DOS METADADOS B2C
# ==============================================================================
@new_lead_ogx.get(
    "/metadados",
    summary="Consultar metadados do formulário B2C",
    tags=[Tag(name="New Lead OGX")],
    description=METADADOS_DESCRIPTION,
    responses=METADADOS_RESPONSES,
)
def buscar_metadados() -> tuple[dict[str, Any], int]:
    """Busca os metadados do formulário B2C para a rota `/new-lead-ogx/metadados`."""
    logger.info("Requisição recebida para buscar metadados B2C")
    payload: Any
    status: int
    payload, status = async_to_sync(cache.get_or_set)(
        key="metadados_b2c",
        fetch=enviar_metadados_b2c,
        baixando="Metadados B2C",
    )
    if status < 200 or status >= 300:
        try:
            status_name: str = HttpStatus(status).name
        except ValueError:
            status_name = "UNKNOWN"
        logger.error(
            "Falha ao buscar metadados B2C | HTTP %s %s", status, status_name
        )
        return payload, status
    else:
        logger.info("Metadados B2C retornados com sucesso")

    cache_entry: dict[str, Any] | None = cache.store.get("metadados_b2c")
    if cache_entry is None:
        logger.error(
            "Metadados B2C não foram armazenados no cache | HTTP %s %s",
            HttpStatus.BAD_GATEWAY.value,
            HttpStatus.BAD_GATEWAY.name,
        )
        return {"error": "Metadados B2C indisponíveis."}, HttpStatus.BAD_GATEWAY

    timestamp: datetime = datetime.fromtimestamp(
        cache_entry["timestamp"], ZoneInfo("America/Sao_Paulo")
    )
    metadata: dict[str, Any] = Metadados.model_validate(
        {**payload, "timestamp": timestamp}
    ).model_dump(mode="json")
    return metadata, status

# ==============================================================================
# DOCUMENTAÇÃO DA ROTA DE CADASTRO
# ==============================================================================
CADASTRO_DESCRIPTION: str = """\
Rota reservada para o cadastro de leads. Ainda não recebe nem valida dados \
e não cria cadastros."""

CADASTRO_RESPONSES: dict[int | str, Any] = {
    200: {"description": "Rota reservada, ainda sem implementação."},
    422: ValidationErrorResponse,
    "default": {
        "description": "Erro HTTP exibido na página genérica de erro.",
        "content": {"text/html": {"schema": {"type": "string"}}},
    },
}

# ==============================================================================
# ROTA RESERVADA PARA CADASTRO DE LEADS
# ==============================================================================
@new_lead_ogx.post(
    "/cadastro",
    summary="Cadastrar lead de interesse",
    tags=[Tag(name="New Lead OGX")],
    description=CADASTRO_DESCRIPTION,
    responses=CADASTRO_RESPONSES,
)
def cadastro_lead() -> None:
    """Representa a rota `/new-lead-ogx/cadastro`, ainda reservada."""
    pass

__all__ = ["new_lead_ogx"]
