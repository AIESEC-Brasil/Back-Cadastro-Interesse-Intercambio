"""Módulo de Exportação de Controllers e Roteadores.

Ponto central para agregação e exposição de todos os controllers
da aplicação Flask. Permite a vinculação direta das rotas no arquivo principal.
"""

# =================================================================
# 1. IMPORTAÇÕES DE CONTROLLERS E ROTEADORES
# =================================================================
from .DivisaoMercadoController import divisao_mercado  # Rotas de escritórios/universidades
from .NewLeadOgxController import new_lead_ogx  # Rotas para captação de leads B2C (OGX)


# =================================================================
# 2. EXPORTAÇÃO CONSOLIDADA VIA __all__
# =================================================================
__all__ = [
    "new_lead_ogx",  # Roteador responsável pelos endpoints de leads B2C (OGX)
    "divisao_mercado",  # Roteador responsável pelos endpoints de divisão de mercado
]