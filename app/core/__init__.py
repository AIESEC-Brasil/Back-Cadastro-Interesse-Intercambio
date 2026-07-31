"""Módulo de Exportação do Core (Core Package).

Centraliza a inicialização de todas as extensões e configurações base do projeto.
Fornece as instâncias globais e utilitários que alimentam o ciclo de vida
da aplicação Flask (Banco de Dados, Migrações, Serialização, Logs e Compressão).
"""

# =================================================================
# 1. IMPORTAÇÕES DE INFRAESTRUTURA E EXTENSÕES
# =================================================================

# Importa o submódulo de configurações dinâmicas de ambiente
from . import config
from .config import *

# Importa o objeto de compressão para otimização de respostas HTTP
from .compress import compress

# Importa a instância central do ORM SQLAlchemy
from .db import db

# Importa a função de inicialização e configuração de logs
from .logger import setup_logging

# Importa a instância do Flask-Migrate (Alembic)
from .migrate import migrate

# Importa a instância do Marshmallow para (de)serialização
from .schema import ma

# =================================================================
# 2. EXPORTAÇÃO CONSOLIDADA VIA __all__
# =================================================================

# O __all__ define o que será exportado ao fazer 'from app.core import *'
# Concatenamos a lista de strings do config.__all__ para manter a interface plana.
__all__ = [
              "compress",  # Instância de compressão HTTP (Flask-Compress)
              "db",  # Instância do ORM (SQLAlchemy)
              "migrate",  # Instância de controle de migrações (Flask-Migrate)
              "ma",  # Instância de serialização de schemas (Flask-Marshmallow)
              "setup_logging",  # Função de inicialização e setup dos loggers
          ] + config.__all__  # Adiciona dinamicamente as variáveis e flags do módulo de ambiente