"""Módulo de exportação de modelos ORM (Models Package).

Ponto central de acesso aos modelos ORM da aplicação.
Este módulo expõe a instância do banco de dados e as entidades responsáveis
pela lógica de Divisão de Mercado, roteamento de vendas e configuração
de escritórios (CLs).
"""

# =================================================================
# 1. IMPORTAÇÕES DE ENTIDADES
# =================================================================
from .divisaoMercadoModel import DivisaoCL, Universidades, db


# =================================================================
# 2. EXPORTAÇÃO CONSOLIDADA VIA __all__
# =================================================================
__all__ = [
    "db",            # Instância do SQLAlchemy (Core)
    "Universidades", # Entidade de mapeamento de mercado por instituição
    "DivisaoCL",     # Entidade de configuração de roteamento por Comitê Local
]