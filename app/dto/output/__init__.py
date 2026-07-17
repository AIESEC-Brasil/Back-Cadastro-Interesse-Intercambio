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
from .httpstatus import HttpStatus
from .metadados import Metadados
from .DivisaoMercado import DivisaoMercadoUniversidades,DivisaoMercadoCl,ListagemEscritoriosRespostaDTOCL

# =================================================================
# Exportação Consolidada
# =================================================================

#

# O __all__ define explicitamente quais classes estarão disponíveis ao importar este pacote.
# Isso facilita o uso em Services e Blueprints: from app.dtos.output import HttpStatus
__all__ = [
    "HttpStatus",                # Enumerador de códigos de status HTTP
    "Metadados",
    "DivisaoMercadoCl",
    "DivisaoMercadoUniversidades",
    "ListagemEscritoriosRespostaDTOCL"
]