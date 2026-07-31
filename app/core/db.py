"""Módulo de Configuração do SQLAlchemy (Database Instance).

Inicialização do ORM SQLAlchemy para a aplicação Flask.
Este módulo disponibiliza a instância global 'db' a ser importada pelos modelos
e camadas que interagem com o banco de dados.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
# O Flask-SQLAlchemy é uma extensão que facilita o uso do SQLAlchemy com Flask,
# oferecendo ferramentas para gerenciar conexões, sessões e modelos.
from flask_sqlalchemy import SQLAlchemy

# =================================================================
# 2. INSTÂNCIA GLOBAL DO BANCO DE DADOS
# =================================================================

# Criação da instância central do banco de dados.
# Nota de arquitetura: Esta instância 'db' deve ser vinculada à aplicação
# principal (app.py ou Application Factory) através do método `db.init_app(app)`.
db = SQLAlchemy()


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================

# O __all__ garante que apenas a instância 'db' seja exposta
# ao importar este módulo via wildcard (from .db import *)
__all__ = ["db"]