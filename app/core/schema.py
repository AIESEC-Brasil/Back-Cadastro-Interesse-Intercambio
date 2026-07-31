"""Módulo de Configuração do Marshmallow.

Inicialização do Marshmallow para (de)serialização e validação de DTOs/Schemas.
Disponibiliza a instância global 'ma' para ser vinculada à aplicação Flask.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
# Flask-Marshmallow integra o Marshmallow ao Flask e ao SQLAlchemy,
# permitindo a criação automática de schemas baseados em tabelas.
from flask_marshmallow import Marshmallow

# =================================================================
# 2. INSTÂNCIA GLOBAL DO MARSHMALLOW
# =================================================================

# Instanciação do objeto Marshmallow.
# Nota de arquitetura: No arquivo principal da aplicação (app.py),
# ele deve ser inicializado via `ma.init_app(app)`
# preferencialmente APÓS a inicialização do Banco de Dados (`db.init_app(app)`).
ma = Marshmallow()


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["ma"]