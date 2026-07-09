"""
Helpers de formatacao especificos da camada de apresentacao/integracao.

Atualmente contem utilitario para construir a URL do Fit Cultural utilizando
hash fragment com os parametros codificados.
"""

# ==============================
# Importacoes (Dependencies)
# ==============================
from urllib.parse import urlencode  # Converte dicionarios em strings de consulta (key=value&...)
from ..config import URL_FIT_CULTURAL # URL base definida nas variaveis de ambiente/configuracao

# ==============================
# Formatadores de Integracao
# ==============================

def payload_podio(data:dict):
    return {"fields": data}

# ==============================
# Exportacoes
# ==============================
__all__ = ["payload_podio"]