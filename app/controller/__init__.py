"""Rota de metadados."""

from .DivisaoMercado import divisao_mercado
from .NewLeadOgxController import cadastro_b2c_view, cadastro_lead_view, new_lead_ogx

# ==============================================================================
# ROTAS REGISTRADAS PELA APLICAÇÃO
# ==============================================================================
__all__ = [
    "cadastro_b2c_view",
    "cadastro_lead_view",
    "divisao_mercado",
    "new_lead_ogx",
]
