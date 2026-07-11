"""
Inicialização do Marshmallow para (de)serialização/validação de schemas.
Exponibiliza a instância global 'ma'.
"""

# ==============================
# Importações (Dependencies)
# ==============================
# Flask-Marshmallow integra o Marshmallow ao Flask e ao SQLAlchemy,
# permitindo a criação automática de schemas baseados em tabelas.
from flask_marshmallow import Marshmallow

# ==============================
# Instância Global
# ==============================

# Criação do objeto Marshmallow.
# Nota: No arquivo principal (app.py), ele deve ser inicializado com ma.init_app(app)
# preferencialmente após a inicialização do Banco de Dados (db.init_app(app)).
ma = Marshmallow()

# ==============================
# Exportações
# ==============================



__all__ = ["ma"]