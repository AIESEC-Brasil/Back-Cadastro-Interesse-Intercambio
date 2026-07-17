"""
Pacote de Clientes Google Apps Script
------------------------------------

Este módulo centraliza as comunicações com os scripts de automação do Google.
Atualmente focado no motor de disparos de e-mail e integração com planilhas
do ecossistema AIESEC.
"""

# =================================================================
# Importações de Submódulos
# =================================================================

# Importa as funções de disparo definidas no arquivo googlescript.py
# como 'enviar_email_psel'.
from .googlescript import *

# =================================================================
# Exportação Consolidada
# =================================================================



# O __all__ herda a lista de exportação do submódulo.
# Isso permite que em qualquer lugar do sistema você use:
# from app.clients.googlescript import enviar_email_psel
__all__ = (
    googlescript.__all__
)