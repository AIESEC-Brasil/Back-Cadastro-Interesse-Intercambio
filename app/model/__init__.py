"""
Models Module
-------------

Ponto central de acesso aos modelos ORM da aplicação.
Este módulo expõe a instância do banco de dados e as entidades responsáveis
pela lógica de Divisão de Mercado, roteamento de vendas e configuração
de escritórios (CLs).
"""

# ==============================
# Importações de Entidades
# ==============================

# Importa a instância do banco e as classes de modelo do arquivo de definição
from .divisaoMercadoModel import db, DivisaoCL, Universidades

# ==============================
# Exportação Consolidada
# ==============================

# O __all__ define a interface pública deste pacote.
# Quando você fizer 'from app.models import *', apenas estes itens serão expostos.
__all__ = [
    "db",            # Instância do SQLAlchemy (Core)
    "Universidades", # Entidade de mapeamento de mercado por instituição
    "DivisaoCL",     # Entidade de configuração de roteamento por Comitê Local
]