"""Flags do ambiente de execução do servidor."""

import asyncio
import logging
from typing import Any

from ..config import AMBIENTE, DOMINIOS_PERMITIDOS


# ==============================================================================
# FLAGS DO AMBIENTE DE EXECUÇÃO
# ==============================================================================
logger: logging.Logger = logging.getLogger(__name__)

IS_DEV: bool = AMBIENTE in {"DEV", "DEVELOPMENT"}
IS_TEST: bool = AMBIENTE in {"TEST", "TESTING"}
IS_PRODUCTION: bool = AMBIENTE in {"PROD", "PRODUCTION"}


# ==============================================================================
# PRÉ-CARREGAMENTO DOS METADADOS
# ==============================================================================
async def pre_carregamento_metadados() -> bool:
    """Busca os metadados B2C, escritórios e universidades no startup e os coloca no cache em memória de forma concorrente."""
    from ..cache import cache
    from ..clients.b2c import enviar_metadados_b2c
    from ..clients.divisao_mercado import (
        enviar_metadados_escritorios,
        enviar_metadados_universidades,
    )

    logger.info("Iniciando pré-carregamento concorrente de todos os metadados")
    # Executa as 3 chamadas em paralelo
    resultados = await asyncio.gather(
        cache.get_or_set(key="metadados_b2c", fetch=enviar_metadados_b2c),
        cache.get_or_set(
            key="metadados_escritorios", fetch=enviar_metadados_escritorios
        ),
        cache.get_or_set(
            key="metadados_universidades", fetch=enviar_metadados_universidades
        ),
        return_exceptions=True,
    )

    sucesso = True

    # Nomes descritivos para facilitar os logs de acompanhamento
    metadados_info = [
        ("B2C", resultados[0]),
        ("Escritórios", resultados[1]),
        ("Universidades", resultados[2]),
    ]

    for nome, resultado in metadados_info:
        if isinstance(resultado, Exception):
            logger.error("Erro inesperado no pré-carregamento de %s: %s", nome, resultado)
            sucesso = False
            continue

        payload, status = resultado

        if not 200 <= status < 300:
            logger.warning(
                "Pré-carregamento de %s falhou com status HTTP %s",
                nome,
                status,
            )
            sucesso = False
            continue

        if isinstance(payload, dict) and isinstance(payload.get("dados"), list):
            total_itens: int = len(payload["dados"])
        else:
            data: Any = payload.get("data", {}) if isinstance(payload, dict) else {}
            fields: list[Any] = (
                data.get("fields", []) if isinstance(data, dict) else []
            )
            total_itens = len(fields)
        logger.info(
            "Pré-carregamento de %s concluído: %s itens em cache",
            nome,
            total_itens,
        )

    return sucesso


__all__ = [
    "IS_DEV",
    "IS_TEST",
    "IS_PRODUCTION",
    "DOMINIOS_PERMITIDOS",
    "pre_carregamento_metadados",
]
