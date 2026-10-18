"""Flags do ambiente de execução do servidor."""

import logging

from ..config import AMBIENTE, DOMINIOS_PERMITIDOS

logger = logging.getLogger(__name__)

IS_DEV = AMBIENTE in {"DEV", "DEVELOPMENT"}
IS_TEST = AMBIENTE in {"TEST", "TESTING"}
IS_PRODUCTION = AMBIENTE in {"PROD", "PRODUCTION"}


async def pre_carregamento_metadados() -> bool:
    """Busca os metadados B2C no startup e os coloca no cache em memória."""
    from ..cache import cache
    from ..clients.b2c import enviar_metadados_b2c

    logger.info("Iniciando pré-carregamento dos metadados B2C")
    payload, status = await cache.get_or_set(
        key="metadados_b2c",
        fetch=enviar_metadados_b2c,
    )

    if not 200 <= status < 300:
        logger.warning(
            "Pré-carregamento dos metadados B2C falhou com status HTTP %s",
            status,
        )
        return False

    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    fields = data.get("fields", []) if isinstance(data, dict) else []
    logger.info("Pré-carregamento concluído: %s campos em cache", len(fields))
    return True


__all__ = [
    "IS_DEV",
    "IS_TEST",
    "IS_PRODUCTION",
    "DOMINIOS_PERMITIDOS",
    "pre_carregamento_metadados",
]
