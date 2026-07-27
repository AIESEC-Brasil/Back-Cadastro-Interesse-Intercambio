"""
Módulo de DTOs (Data Transfer Objects) - Divisão de Mercado.

Este módulo define as estruturas de validação e serialização de dados para as
divisões de mercado da AIESEC. Ele resolve o problema de herança múltipla no
Pydantic: as classes "Wrapper" precisam do método 'processar_lista', mas não podem
herdar os campos físicos (como 'id', 'nome') para não quebrar a validação.
"""

from pydantic import (
    BaseModel,       # Classe base do Pydantic para criação de modelos/containers de dados.
    Field,           # Utilizado para definir metadados dos campos, descrições, aliases e exemplos para o JSON Schema.
    model_validator
)

from typing import (
    List,            # Hint de tipo para representar listas/arrays de elementos.
    Any              # Tipo flexível para aceitar qualquer payload de dados brutos do Podio.
)

# Importa o modelo base de item individual (que contém campos como id, nome, gv, gt)
from ..globals import DivisaoMercado


# =================================================================================
# MIXIN DE COMPORTAMENTO (DESIGN PATTERN)
# =================================================================================
class ProcessadorListaMixin:
    """
    Mixin que fornece a capacidade de processamento de listas vindas do Podio.

    Herdar desta classe garante que o DTO wrapper tenha o método 'processar_lista'
    disponível no seu namespace, sem herdar os campos de dados individuais
    (evitando erros de 'Parameter unfilled' no Pydantic).
    """

    @classmethod
    def processar_lista(cls, dados_brutos: Any) -> List[DivisaoMercado]:
        """
        Delega o processamento da lista para a implementação de DivisaoMercado.

        Isso garante consistência e reaproveita a transformação de metadados
        original definida no modelo de domínio.
        """
        # Se 'DivisaoMercado' já possui o método original, nós o reaproveitamos dinamicamente
        if hasattr(DivisaoMercado, "processar_lista"):
            return DivisaoMercado.processar_lista(dados_brutos)

        # Caso o método não exista no destino, gera um alerta explícito de desenvolvimento
        raise NotImplementedError(
            "O método 'processar_lista' não foi encontrado na classe original 'DivisaoMercado'."
        )


# =================================================================================
# WRAPPERS (CONTAINERS) DE DADOS
# =================================================================================
# NOTA DE DESIGN: Herdamos de 'BaseModel' para a estrutura de validação e de
# 'ProcessadorListaMixin' para ganhar o método de processamento sem herdar atributos.
# =================================================================================

class DivisaoMercadoUniversidades(BaseModel, ProcessadorListaMixin):
    """
    Wrapper de dados que envelopa a lista de universidades cadastradas.

    Herda 'ProcessadorListaMixin' para expor o método 'processar_lista' na rota.
    """

    universidades: List[DivisaoMercado] = Field(
        title="Universidades",
        description="Mapeamento completo de universidades brasileiras e seus respectivos roteamentos.",
        json_schema_extra={
            "type": "object",
            "example": [
                {
                    "nome": "Universidade Exemplo",
                    "gv": "Roteamento GV Exemplo",
                    "gt": "Roteamento GT Exemplo",
                    "id": "ID da Universidade Exemplo"
                },
                {
                    "nome": "Universidade Exemplo",
                    "gv": "Roteamento GV Exemplo",
                    "gt": "Roteamento GT Exemplo",
                    "id": "ID da Universidade Exemplo"
                }
            ]
        }
    )


class DivisaoMercadoCl(BaseModel, ProcessadorListaMixin):
    """
    Wrapper de dados que envelopa a lista de Comitês Locais (CLs) cadastrados.

    Herda 'ProcessadorListaMixin' para expor o método 'processar_lista' na rota.
    """

    cl: List[DivisaoMercado] = Field(
        title="Comitê Local (CL)",
        description="Informações de roteamento e configuração ativa de cada Comitê Local (CL).",
        json_schema_extra={
            "type": "object",
            "example": [
                {
                    "nome": "Comitê Local Exemplo",
                    "gv": "Roteamento GV Exemplo",
                    "gt": "Roteamento GT Exemplo",
                    "id": "ID do Comitê Local Exemplo"
                },
                {
                    "nome": "Comitê Local Exemplo",
                    "gv": "Roteamento GV Exemplo",
                    "gt": "Roteamento GT Exemplo",
                    "id": "ID do Comitê Local Exemplo"
                }
            ]
        }
    )

class PaginacaoMetaDTO(BaseModel):
    """Mapeia os metadados estruturais da paginação vinda do SQLAlchemy."""
    current_page: int = Field(..., description="Índice da página atual da consulta.")
    limit: int = Field(..., description="Quantidade máxima de registros por página.")
    total_items: int = Field(..., description="Quantidade total de registros encontrados no banco.")
    total_pages: int = Field(..., description="Quantidade total de páginas disponíveis.")
    has_next: bool = Field(..., description="Indicativo se existe uma próxima página disponível.")
    has_prev: bool = Field(..., description="Indicativo se existe uma página anterior disponível.")


class ListagemEscritoriosRespostaDTOCL(BaseModel):
    """Modelo principal que unifica e valida o payload completo de retorno reaproveitando o tipo existente."""
    data: DivisaoMercadoCl = Field(..., description="Lista contendo os escritórios e seus respectivos mercados.")
    pagination: PaginacaoMetaDTO = Field(..., description="Metadados de controle da paginação.")

    # Configuração do Pydantic v2 para aceitar os aliases e manter os nomes originais se necessário
    model_config = {
        "populate_by_name": True
    }

class ListagemEscritoriosRespostaDTOUniversidades(BaseModel):
    """Modelo principal que unifica e valida o payload completo de retorno reaproveitando o tipo existente."""
    data: DivisaoMercadoUniversidades = Field(..., description="Lista contendo os escritórios e seus respectivos mercados.")
    pagination: PaginacaoMetaDTO = Field(..., description="Metadados de controle da paginação.")

    # Configuração do Pydantic v2 para aceitar os aliases e manter os nomes originais se necessário
    model_config = {
        "populate_by_name": True
    }

__all__ = ["DivisaoMercadoCl","DivisaoMercadoUniversidades","ListagemEscritoriosRespostaDTOCL","ListagemEscritoriosRespostaDTOUniversidades"]