"""Módulo de exportação de roteamento (Router).

Fornece acesso público à classe Router estendida do APIBlueprint,
utilizada para definição de rotas, middlewares e documentação OpenAPI.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from .router import ApiOpenAPI, Router


# =================================================================
# 2. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["ApiOpenAPI", "Router"]
