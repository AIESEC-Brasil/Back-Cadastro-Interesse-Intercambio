"""Pacote de DTOs de Entrada (Input Models).

Centraliza e exporta os modelos de dados utilizados para validar
e tipar as entradas de dados no fluxo do Processo Seletivo (PSEL).
"""

# =================================================================
# 1. IMPORTAÇÕES DE SUBMÓDULOS E DTOS DE ENTRADA
# =================================================================

# Importa os DTOs de entrada para o fluxo de pré-cadastro de Leads
from .LeadCadastroDTO import (
    CriarPreCadastroLead,
    LeadPreCadastroInput,
)

# =================================================================
# 2. EXPORTAÇÃO CONSOLIDADA DO PACOTE
# =================================================================

# O __all__ define a interface pública deste pacote.
# Ao estruturar o __all__, garantimos que ao fazer 'from inputs import *',
# apenas as classes autorizadas sejam expostas.
__all__ = [
    "LeadPreCadastroInput",
    "CriarPreCadastroLead",
]