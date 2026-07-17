from .api_doc import api
from .v1 import v1

# Registra o módulo da Versão 1 no roteador principal.
api.register_api(v1)

__all__ = ["api"]