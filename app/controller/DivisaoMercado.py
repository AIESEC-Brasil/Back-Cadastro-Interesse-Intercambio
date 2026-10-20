"""Endpoints de metadados para divisão de mercado."""

import logging
from datetime import datetime
from typing import Any, Callable
from zoneinfo import ZoneInfo

from asgiref.sync import async_to_sync
from flask_openapi3 import Tag

from ..cache import cache
from ..clients.divisao_mercado import (
    enviar_metadados_escritorios,
    enviar_metadados_universidades,
)
from ..dto import HttpStatus
from ..dto.output import DivisaoMercadoMetadados
from ..router import Router


divisao_mercado: Router = Router(
    name="divisao_mercado",
    url_prefix="/divisao-mercado",
)
logger: logging.Logger = logging.getLogger(__name__)

METADADOS_RESPONSES: dict[int | str, Any] = {
    200: DivisaoMercadoMetadados,
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


def _buscar_metadados(
    *,
    key: str,
    fetch: Callable[[], Any],
    label: str,
) -> tuple[dict[str, Any], int]:
    """Obtém os metadados do cache ou consulta a origem configurada."""
    logger.info("Requisição recebida para buscar %s", label)
    payload: Any
    status: int
    payload, status = async_to_sync(cache.get_or_set)(
        key=key,
        fetch=fetch,
        baixando=label,
    )
    if status < 200 or status >= 300:
        try:
            status_name: str = HttpStatus(status).name
        except ValueError:
            status_name = "UNKNOWN"
        logger.error("Falha ao buscar %s | HTTP %s %s", label, status, status_name)
        return payload, status

    cache_entry: dict[str, Any] | None = cache.store.get(key)
    if cache_entry is None:
        logger.error(
            "%s não foram armazenados no cache | HTTP %s %s",
            label,
            HttpStatus.BAD_GATEWAY.value,
            HttpStatus.BAD_GATEWAY.name,
        )
        return {"error": f"{label} indisponíveis."}, HttpStatus.BAD_GATEWAY

    timestamp: datetime = datetime.fromtimestamp(
        cache_entry["timestamp"], ZoneInfo("America/Sao_Paulo")
    )
    logger.info("%s retornados com sucesso", label)
    return {**payload, "timestamp": timestamp}, status


@divisao_mercado.get(
    "/escritorios/metadados",
    summary="Consultar metadados de escritórios",
    tags=[Tag(name="Metadados")],
    responses=METADADOS_RESPONSES,
)
def buscar_metadados_escritorios() -> tuple[dict[str, Any], int]:
    """Busca os metadados de escritórios."""
    return _buscar_metadados(
        key="metadados_escritorios",
        fetch=enviar_metadados_escritorios,
        label="Metadados de escritórios",
    )


@divisao_mercado.get(
    "/universidades/metadados",
    summary="Consultar metadados de universidades",
    tags=[Tag(name="Metadados")],
    responses=METADADOS_RESPONSES,
)
def buscar_metadados_universidades() -> tuple[dict[str, Any], int]:
    """Busca os metadados de universidades."""
    return _buscar_metadados(
        key="metadados_universidades",
        fetch=enviar_metadados_universidades,
        label="Metadados de universidades",
    )


__all__ = ["divisao_mercado"]