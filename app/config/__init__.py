"""Configurações públicas do serviço de metadados."""

from .settings import (
    AMBIENTE,
    APPSCRIPT_B2C,
    APPSCRIPT_DIVISAO_MERCADO,
    API_KEYS_PERMITIDAS,
    CACHE_TTL,
    DOMINIOS_PERMITIDOS,
)

__all__ = [
    "AMBIENTE", "APPSCRIPT_B2C", "API_KEYS_PERMITIDAS",
    "APPSCRIPT_DIVISAO_MERCADO",
    "CACHE_TTL", "DOMINIOS_PERMITIDOS",
]
