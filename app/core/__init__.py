"""Flags do ambiente."""

from .config import (
    DOMINIOS_PERMITIDOS,
    IS_DEV,
    IS_PRODUCTION,
    IS_TEST,
    pre_carregamento_metadados,
)
from .logger import setup_logging

__all__ = [
    "DOMINIOS_PERMITIDOS",
    "IS_DEV",
    "IS_PRODUCTION",
    "IS_TEST",
    "pre_carregamento_metadados",
    "setup_logging",
]
