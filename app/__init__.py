"""
Aplicação Flask de metadados B2C.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask_openapi3 import OpenAPI


def create_app() -> OpenAPI:
    """Cria a aplicação sem importar sua configuração até a chamada da factory."""
    from .main import create_app as create_app_factory

    return create_app_factory()

# ==============================================================================
# API PÚBLICA DO PACOTE
# ==============================================================================
__all__ = ["create_app"]
