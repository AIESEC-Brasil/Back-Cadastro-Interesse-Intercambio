"""
Pacote de DTOs de Saída (Output Models).
---------------------------------------

Centraliza e exporta os modelos de resposta, enums de status HTTP e
envelopes de integração para APIs externas.
"""

# =================================================================
# Importações de Submódulos
# =================================================================

# Importa todos os modelos de resposta definidos no módulo psel
# (HttpStatus, ModelPodio, ReponsePselPreCadastro, etc.)
from .psel_output import *
from .httpstatus import HttpStatus

# =================================================================
# Exportação Consolidada
# =================================================================

#

# O __all__ define explicitamente quais classes estarão disponíveis ao importar este pacote.
# Isso facilita o uso em Services e Blueprints: from app.dtos.output import HttpStatus
__all__ = [
    "ReponseOutPutPreCadastro", # Envelope principal de resposta da API
    "HttpStatus"                # Enumerador de códigos de status HTTP
]