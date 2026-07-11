"""
Core Package
------------

Centraliza a inicialização de todas as extensões e configurações base do projeto.
Fornece as instâncias globais que alimentam o ciclo de vida da aplicação Flask.
"""

# =================================================================
# Importações de Infraestrutura (Instâncias Globais)
# =================================================================

# Importa as configurações derivadas de ambiente (CORS, DB_CONNECT, etc.)
from .config import *

# Importa a função de configuração de logs (App, Audit, Werkzeug)
from .logger import *

# Importa o objeto de compressão para otimizar respostas HTTP
from .compress import compress  # Instancia o objeto de compressão para otimizar respostas HTTP

from .db import db

from .migrate import migrate

from .schema import ma

# =================================================================
# Exportação Consolidada
# =================================================================

# 

# O __all__ define o que será exportado ao fazer 'from app.core import *'
# Nota: Concatenamos a lista de strings do config.__all__ para manter a interface plana.
__all__ = [
    "compress",        # Instância de compressão para otimizar respostas HTTP
    "db",              # Instância SQLAlchemy
    "migrate",         # Instância Flask-Migrate
    "ma",              # Instância Marshmallow
    "setup_logging",   # Função de inicialização de logs
] + config.__all__ # Adiciona dinamicamente as variáveis de config ao export