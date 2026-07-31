"""Submódulo de Paginação e Listagens - AIESEC Gateway (V1).

Ponto de agregação dos roteadores de consulta paginada da API.
Importa e expõe os submódulos de escritórios (CLs) e universidades.
"""

# ==============================================================================
# 1. IMPORTAÇÕES DOS ROTEADORES LOCAIS
# ==============================================================================

# Importa o roteador responsável pelas consultas e paginação de escritórios
from .escritorios import escritorios

# Importa o roteador responsável pelas consultas e paginação de universidades
from .universidades import universidades


# ==============================================================================
# 2. EXPORTAÇÃO CONSOLIDADA E CONTRATO PÚBLICO
# ==============================================================================

# Limita e expõe explicitamente os dois roteadores registrados para o pacote v1
__all__ = [
    "escritorios",     # Roteador com endpoints de paginação de escritórios (CLs)
    "universidades",   # Roteador com endpoints de paginação de universidades
]