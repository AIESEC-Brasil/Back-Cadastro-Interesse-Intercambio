"""
config
------

Módulo de configuração global da aplicação.
Este arquivo facilita o acesso às variáveis de ambiente e constantes
definidas no submódulo 'settings'.
"""

# =================================================================
# Importações de Configurações
# =================================================================

# Importa todas as variáveis validadas (DB, API Keys, Podio Tokens, etc.)
# definidas no arquivo settings.py
from .settings import *

# =================================================================
# Exportação Consolidada
# =================================================================

#

# O __all__ define a interface pública deste pacote.
# Nota: Aqui usamos a lista de strings definida em settings.__all__
# para que o acesso seja feito de forma limpa: from app.config import AMBIENTE
__all__ = settings.__all__