"""Módulo de Configuração do Flask-Migrate.

Inicialização do Flask-Migrate (integração com Alembic) para controle de versão
e migrações de banco de dados.
Disponibiliza a instância global 'migrate'.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
# O Flask-Migrate lida com o controle de versão do banco de dados SQLAlchemy
# através da interface de linha de comando (CLI) ou automações.
from flask_migrate import Migrate

# =================================================================
# 2. INSTÂNCIA GLOBAL DO FLASK-MIGRATE
# =================================================================

# Criação do objeto Migrate.
# Nota de arquitetura: No arquivo principal da aplicação (app.py),
# ele deve ser vinculado à aplicação e ao banco de dados via `migrate.init_app(app, db)`.
migrate = Migrate()


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["migrate"]