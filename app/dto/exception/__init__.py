"""Pacote de DTOs para Tratamento e Respostas de Exceções.

Centraliza e re-exporta todas as estruturas de respostas de erro,
tratamentos de exceções do Pydantic/Werkzeug e mapeamentos dinâmicos
para a camada de apresentação da API.
"""

# =================================================================
# 1. IMPORTAÇÕES E RE-EXPORTAÇÃO DE EXCEÇÕES
# =================================================================

# Importa o módulo relativo para ter acesso às suas definições internas
from . import exceptionsDTO

# Importa todos os elementos do arquivo de DTOs de exceções
from .exceptionsDTO import *

# =================================================================
# 2. EXPORTAÇÃO CONSOLIDADA DO PACOTE
# =================================================================

# Re-exporta a lista pública exata definida em exceptionsDTO.__all__
__all__ = exceptionsDTO.__all__