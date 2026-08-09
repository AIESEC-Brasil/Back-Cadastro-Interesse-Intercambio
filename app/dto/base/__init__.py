"""
Módulo de exportação do DTO Base de Cadastro de Leads.

Este módulo centraliza e re-exporta os componentes e definições contidos em
`leadCadastroBaseDTO`, fornecendo uma interface limpa e simplificada para
a importação das estruturas base de cadastro na aplicação.
"""

# =================================================================
# 1. IMPORTAÇÕES E RE-EXPORTAÇÕES
# =================================================================

from . import leadCadastroBaseDTO
from .leadCadastroBaseDTO import *

# =================================================================
# 2. EXPORTAÇÃO CONSOLIDADA DO MÓDULO
# =================================================================

__all__ = leadCadastroBaseDTO.__all__