"""Módulo de exportação de esquemas de Divisão de Mercado.

Reexporta todas as instâncias e classes expostas pelo submódulo DivisaoMercadoSchema.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from .DivisaoMercadoSchema import *  # Importa todas as definições expostas
from . import DivisaoMercadoSchema  # Importa o submódulo para acesso ao __all__

# =================================================================
# 2. EXPORTAÇÃO DO MÓDULO
# =================================================================
# Reexporta a lista contida no __all__ do submódulo DivisaoMercadoSchema
__all__ = DivisaoMercadoSchema.__all__