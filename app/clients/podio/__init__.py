"""
Pacote de Clientes Podio
------------------------

Este módulo centraliza as funcionalidades de integração com o CRM Podio.
Ele expõe todas as funções validadas para manipulação de leads e autenticação.
"""

# =================================================================
# Importações de Submódulos
# =================================================================

# Importa todas as funções definidas em psel_input.py (ou podio.py, dependendo do arquivo)
# como getAcessToken, adicionar_lead, atualizar_lead, etc.
from .podio import *

# =================================================================
# Exportação Consolidada
# =================================================================



# O __all__ aqui herda a lista de exportação definida dentro do submódulo 'podio'.
# Isso permite que ao importar o pacote (ex: from app.clients.podio import *),
# apenas as funções de negócio pretendidas sejam expostas, mantendo o encapsulamento.
__all__ = (
    podio.__all__
)