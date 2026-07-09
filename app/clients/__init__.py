"""
Pacote de Integrações Externas (Clients)
----------------------------------------

Este módulo consolida os clientes de comunicação para APIs de terceiros.
Utiliza a técnica de agregação para simplificar as importações em outras camadas.
"""

# =================================================================
# Importações de Submódulos (Clientes Especializados)
# =================================================================

# Importa o cliente HTTP base (HttpClient)
from .http_request import *

# Importa o cliente de integração com o CRM Podio (Auth, Items, etc.)
from .podio import *

# =================================================================
# Exportação Consolidada
# =================================================================



# O __all__ aqui é construído dinamicamente concatenando as listas
# de exportação de cada submódulo. Isso garante que apenas as classes
# públicas (como HttpClient, GoogleScriptClient, PodioClient) sejam expostas.
__all__ = (
        http_request.__all__ +
        podio.__all__
)