"""Módulo de Exportação de Migrações (Migrations Package).

Ponto central para gestão de versões do banco de dados.
Expõe as funcionalidades de automação de esquema e sincronização ORM.
"""

# =================================================================
# 1. IMPORTAÇÕES DE GESTÃO DE BANCO
# =================================================================

# migration: Função orquestradora que gerencia CLI e setup inicial
# upgrade: Função do Flask-Migrate para aplicar mudanças pendentes
from .manager import migration, upgrade


# =================================================================
# 2. EXPORTAÇÃO CONSOLIDADA VIA __all__
# =================================================================

# O __all__ permite que estas funções sejam acessadas diretamente
# via 'from app.migrations import migration'
__all__ = [
    "migration",
    "upgrade",
]