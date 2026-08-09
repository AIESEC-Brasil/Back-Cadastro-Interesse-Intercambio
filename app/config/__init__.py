"""Módulo de Exportação de Configurações (Config Package).

Ponto central de acesso para as variáveis de ambiente e constantes
validadas no submódulo 'settings'. Facilita o acesso limpo via
`from app.config import AMBIENTE`.
"""

# =================================================================
# 1. IMPORTAÇÕES DE CONFIGURAÇÕES E CONSTANTES
# =================================================================

# Importa o módulo settings para acesso às suas exportações
from . import settings

# Importação explícita das constantes para exposição e verificação de tipos
from .settings import (
    AMBIENTE,
    API_KEYS_PERMITIDAS,
    APP_ID,
    APP_TOKEN,
    APPSCRIPT_EXPA,
    CACHE_TTL,
    CLIENT_ID,
    CLIENT_SECRET,
    DB_CONNECT,
    DB_POOL_PRE_PING,
    DB_POOL_RECYCLE,
    DOMINIOS_PERMITIDOS,
    TOKEN_EXPA,
)

# =================================================================
# 2. EXPORTAÇÃO CONSOLIDADA VIA __all__
# =================================================================

# O __all__ define a interface pública exportada por este pacote.
# Reutiliza dinamicamente a lista de strings definida em settings.__all__.
__all__ = settings.__all__