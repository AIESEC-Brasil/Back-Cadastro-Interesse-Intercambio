"""
Inicialização do Flask-Migrate (integração Alembic) para migrações de banco.
Exponibiliza a instância global 'migrate'.
"""

# ==============================
# Importações (Dependencies)
# ==============================
# O Flask-Migrate lida com o controle de versão do banco de dados SQLAlchemy
# através da interface de linha de comando (CLI) ou automações.
from flask_migrate import Migrate

# ==============================
# Instância Global
# ==============================



# Criação do objeto Migrate.
# Importante: No arquivo principal (app.py), ele deve ser vinculado ao app e ao db
# através de: migrate.init_app(app, db)
migrate = Migrate()

# ==============================
# Exportações
# ==============================

__all__ = ["migrate"]