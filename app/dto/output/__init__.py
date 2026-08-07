"""Pacote de DTOs de Saída (Output Models).

Centraliza e exporta os modelos de resposta, enums de status HTTP e
envelopes de integração para APIs externas.
"""

# =================================================================
# 1. IMPORTAÇÕES DE SUBMÓDULOS E DTOS DE SAÍDA
# =================================================================

# Importa o enumerador de códigos de status HTTP customizado da aplicação
from .httpStatusDTO import HttpStatus

# Importa o modelo de gerenciamento de metadados e logs brutos
from .metadadosDTO import Metadados

# Importa os wrappers de resposta para Divisão de Mercado (CLs e Universidades)
from .divisaoMercadoDTO import (
    DivisaoMercadoCl,
    DivisaoMercadoUniversidades,
    ListagemEscritoriosRespostaDTOCL,
    ListagemEscritoriosRespostaDTOUniversidades,
)

# Importa o DTO de saída para pré-cadastro de leads
from .leadCadastroDTO import LeadPreCadastroOutput

# Importa os modelos e a classe de serviço para detecção de conflitos de leads
from .conflitoDTO import (
    ConflitosLeadOutput,
    VerificadorConflitos,
)

# Modelo de tipo generico
from .genericoDTO import *

# =================================================================
# 2. EXPORTAÇÃO CONSOLIDADA DO PACOTE
# =================================================================

# Define explicitamente a API pública exposta ao importar o pacote via wildcard (`from .import *`)
# ou para referências diretas do pacote (`from app.dtos.output import HttpStatus`).
__all__ = [
    "HttpStatus",
    "Metadados",
    "DivisaoMercadoCl",
    "DivisaoMercadoUniversidades",
    "ListagemEscritoriosRespostaDTOCL",
    "ListagemEscritoriosRespostaDTOUniversidades",
    "LeadPreCadastroOutput",
    "ConflitosLeadOutput",
    "VerificadorConflitos",
    "RetornoGenerico"
]