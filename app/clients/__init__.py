"""Pacote de Integrações Externas (Clients).

Consolida e expõe os clientes de comunicação para APIs de terceiros (Podio,
HTTP Base, etc.). Utiliza a técnica de agregação centralizada para simplificar
as importações na camada de serviços da aplicação.
"""

# =================================================================
# 1. IMPORTAÇÕES DOS SUBMÓDULOS DE INTEGRAÇÃO
# =================================================================

# Importa os módulos para acesso direto às suas variáveis de controle (__all__)
from . import http_request, podio

# Importação explícita das classes públicas expostas pelos submódulos
from .http_request import HttpClient
from .podio import *


# =================================================================
# 2. EXPORTAÇÃO CONSOLIDADA VIA __all__
# =================================================================

# Concatena dinamicamente as interfaces públicas de cada cliente especializado,
# garantindo que apenas as classes autorizadas sejam expostas.
__all__ = list(
    http_request.__all__ + podio.__all__
)