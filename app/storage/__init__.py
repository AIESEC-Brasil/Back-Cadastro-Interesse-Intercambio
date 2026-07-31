"""Módulo de exportação do repositório em memória (Storage).

Fornece acesso à instância compartilhada (Singleton) do gerenciador de IPs
autorizados para ser consumida por middlewares, decorators e rotas.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from .storage import storage  # Importa a instância Singleton do módulo storage local


# =================================================================
# 2. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["storage"]