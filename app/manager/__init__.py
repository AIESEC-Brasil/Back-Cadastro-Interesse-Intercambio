"""
Migrations Module
-----------------

Ponto central para gestão de versões do banco de dados.
Expõe as funcionalidades de automação de esquema e sincronização ORM.
"""

# ==============================
# Importações de Gestão
# ==============================

# migration: Função orquestradora que gerencia CLI e setup inicial
# upgrade: Função do Flask-Migrate para aplicar mudanças pendentes
from .manager import migration, upgrade

# ==============================
# Exportação Consolidada
# ==============================

# O __all__ permite que estas funções sejam acessadas diretamente
# via 'from app.migrations import migration'
__all__ = [
    "migration",
    "upgrade"
]