"""Módulo de exportação de serviços de cadastro de leads.

Fornece acesso público às funções de serviço responsável pelo fluxo de
pré-cadastro, verificação de duplicidade e validação de conflitos de leads.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from .CadastrarLeadService import cadastrar_lead  # Importa a função de serviço de cadastro


# =================================================================
# 2. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["cadastrar_lead"]