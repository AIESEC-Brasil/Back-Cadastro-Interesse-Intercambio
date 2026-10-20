"""Rota de metadados."""

from .DivisaoMercado import divisao_mercado
from .NewLeadOgxController import cadastro_lead_view, new_lead_ogx

__all__ = ["cadastro_lead_view", "divisao_mercado", "new_lead_ogx"]
