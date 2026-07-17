"""
Inicialização do SQLAlchemy para a aplicação Flask.

Este módulo expõe a instância global 'db' a ser importada pelos modelos e
camadas que interagem com o banco de dados.
"""

# ==============================
# Importações (Dependencies)
# ==============================
# O Flask-SQLAlchemy é uma extensão que facilita o uso do SQLAlchemy com Flask,
# oferecendo ferramentas para gerenciar conexões, sessões e modelos.
from flask_sqlalchemy import SQLAlchemy

# ==============================
# Instância Global
# ==============================



# Criação da instância central do banco de dados.
# Nota: Esta instância 'db' deve ser vinculada à aplicação no seu app.py
# através do método: db.init_app(app)
db = SQLAlchemy()

# ==============================
# Exportações
# ==============================

# O __all__ garante que apenas a instância 'db' seja exposta
# ao importar este módulo via wildcard (from .db import *)
__all__ = ["db"]