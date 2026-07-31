"""Módulo de exportação pública de repositórios de Divisão de Mercado.

Reexporta as funções assíncronas de consulta ao banco de dados para obter
registros de universidades e escritórios locais (CLs).
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from .buscarRepository import (  # Importa funções de consulta do repositório local
    buscar_todas_universidades,
    buscar_todos_cl,
)


# =================================================================
# 2. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = [
    "buscar_todas_universidades",
    "buscar_todos_cl",
]