"""
Pacote de DTOs de Entrada (Input Models).
----------------------------------------

Centraliza e exporta os modelos de dados utilizados para validar
e tipar as entradas de dados no fluxo do Processo Seletivo (PSEL).
"""

# =================================================================
# Importações de Submódulos
# =================================================================

# Importa todos os modelos definidos no módulo psel (LeadPselInput, ParamsInput, etc.)
from .psel_input import *
from .padrao import Metadados
# =================================================================
# Exportação Consolidada
# =================================================================

# O __all__ define a interface pública deste pacote.
# Ao herdar a lista psel.__all__, garantimos que ao fazer
# 'from inputs import *', apenas as classes autorizadas sejam expostas.
__all__ = ["Metadados"] + psel_input.__all__