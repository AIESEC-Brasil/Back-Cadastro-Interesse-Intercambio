"""Flags do ambiente."""

from typing import Any


def __getattr__(name: str) -> Any:
    """Carrega configurações sob demanda para permitir inicializar logging antes."""
    if name == "setup_logging":
        from .logger import setup_logging

        return setup_logging

    if name in {
        "DOMINIOS_PERMITIDOS",
        "IS_DEV",
        "IS_PRODUCTION",
        "IS_TEST",
        "pre_carregamento_metadados",
    }:
        from . import config

        return getattr(config, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# ==============================================================================
# CONFIGURAÇÃO DE AMBIENTE E LOGGING
# ==============================================================================
__all__ = [
    "DOMINIOS_PERMITIDOS",
    "IS_DEV",
    "IS_PRODUCTION",
    "IS_TEST",
    "pre_carregamento_metadados",
    "setup_logging",
]
