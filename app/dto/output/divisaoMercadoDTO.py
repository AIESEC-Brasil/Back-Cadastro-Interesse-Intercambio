"""Módulo de DTOs (Data Transfer Objects) - Divisão de Mercado.

Este módulo define as estruturas de validação e serialização de dados para as
divisões de mercado da AIESEC. Ele resolve o problema de herança múltipla no
Pydantic: as classes "Wrapper" precisam do método 'processar_lista', mas não podem
herdar os campos físicos (como 'id', 'nome') para não quebrar a validação.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from typing import (
    Any,   # Tipo flexível para aceitar qualquer payload de dados brutos do Podio.
    List,  # Hint de tipo para representar listas/arrays de elementos.
)

from pydantic import (
    BaseModel,  # Classe base do Pydantic para criação de modelos/containers de dados.
    ConfigDict, # Objeto de configuração para definir comportamentos do modelo.
    Field,      # Utilizado para definir metadados dos campos, descrições, aliases e exemplos para o JSON Schema.
)

# Importa o modelo base de item individual (que contém campos como id, nome, gv, gt)
from ..globals import DivisaoMercado


# =================================================================================
# 2. MIXIN DE COMPORTAMENTO (DESIGN PATTERN)
# =================================================================================

class ProcessadorListaMixin:
    """Mixin que fornece a capacidade de processamento de listas vindas do Podio.

    Herdar desta classe garante que o DTO wrapper tenha o método 'processar_lista'
    disponível no seu namespace, sem herdar os campos de dados individuais
    (evitando erros de 'Parameter unfilled' no Pydantic).
    """

    @classmethod
    def processar_lista(cls, dados_brutos: Any) -> List[DivisaoMercado]:
        """Delega o processamento da lista para a implementação de DivisaoMercado.

        Isso garante consistência e reaproveita a transformação de metadados
        original definida no modelo de domínio.

        Args:
            dados_brutos (Any): Payload bruto contendo as opções extraídas do Podio.

        Returns:
            List[DivisaoMercado]: Lista de instâncias validadas de DivisaoMercado.

        Raises:
            NotImplementedError: Caso o método 'processar_lista' não esteja presente em DivisaoMercado.
        """
        # Se 'DivisaoMercado' já possui o método original, nós o reaproveitamos dinamicamente
        if hasattr(DivisaoMercado, "processar_lista"):
            return DivisaoMercado.processar_lista(dados_brutos)

        # Caso o método não exista no destino, gera um alerta explícito de desenvolvimento
        raise NotImplementedError(
            "O método 'processar_lista' não foi encontrado na classe original 'DivisaoMercado'."
        )


# =================================================================================
# 3. WRAPPERS (CONTAINERS) DE DADOS DE MERCADO
# =================================================================================
# NOTA DE DESIGN: Herdamos de 'BaseModel' para a estrutura de validação e de
# 'ProcessadorListaMixin' para ganhar o método de processamento sem herdar atributos.
# =================================================================================

class DivisaoMercadoUniversidades(BaseModel, ProcessadorListaMixin):
    """Wrapper de dados que envelopa a lista de universidades cadastradas.

    Herda 'ProcessadorListaMixin' para expor o método 'processar_lista' na rota.

    Attributes:
        universidades (List[DivisaoMercado]): Lista contendo o mapeamento das universidades brasileiras.
    """

    # Lista de mapeamento de universidades e suas respectivas regras de roteamento
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
                    "id": "ID da Universidade Exemplo",
                },
                {
                    "nome": "Universidade Exemplo",
                    "gv": "Roteamento GV Exemplo",
                    "gt": "Roteamento GT Exemplo",
                    "id": "ID da Universidade Exemplo",
                },
            ],
        },
    )


class DivisaoMercadoCl(BaseModel, ProcessadorListaMixin):
    """Wrapper de dados que envelopa a lista de Comitês Locais (CLs) cadastrados.

    Herda 'ProcessadorListaMixin' para expor o método 'processar_lista' na rota.

    Attributes:
        cl (List[DivisaoMercado]): Lista contendo o mapeamento dos comitês locais ativos.
    """

    # Lista de comitês locais e suas respectivas regras de roteamento
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
                    "id": "ID do Comitê Local Exemplo",
                },
                {
                    "nome": "Comitê Local Exemplo",
                    "gv": "Roteamento GV Exemplo",
                    "gt": "Roteamento GT Exemplo",
                    "id": "ID do Comitê Local Exemplo",
                },
            ],
        },
    )


# =================================================================================
# 4. DTOS DE PAGINAÇÃO E RESPOSTAS UNIFICADAS DE LISTAGEM
# =================================================================================

class PaginacaoMetaDTO(BaseModel):
    """Mapeia os metadados estruturais da paginação vinda do SQLAlchemy.

    Attributes:
        current_page (int): Número da página atual da consulta.
        limit (int): Quantidade máxima de registros retornados por página.
        total_items (int): Quantidade total de registros encontrados na base.
        total_pages (int): Quantidade total de páginas disponíveis.
        has_next (bool): Indica se há uma próxima página de resultados.
        has_prev (bool): Indica se há uma página anterior de resultados.
    """

    # Número da página atual retornado na consulta paginada
    current_page: int = Field(..., description="Índice da página atual da consulta.")

    # Limite máximo de itens por página configurado na consulta
    limit: int = Field(..., description="Quantidade máxima de registros por página.")

    # Total absoluto de registros encontrados no banco de dados para os filtros aplicados
    total_items: int = Field(..., description="Quantidade total de registros encontrados no banco.")

    # Quantidade total de páginas calculadas
    total_pages: int = Field(..., description="Quantidade total de páginas disponíveis.")

    # Flag booleana indicando a presença de próxima página
    has_next: bool = Field(..., description="Indicativo se existe uma próxima página disponível.")

    # Flag booleana indicando a presença de página anterior
    has_prev: bool = Field(..., description="Indicativo se existe uma página anterior disponível.")


class ListagemEscritoriosRespostaDTOCL(BaseModel):
    """Modelo principal que unifies e valida o payload completo de retorno para Comitês Locais (CL).

    Attributes:
        data (DivisaoMercadoCl): Wrapper envelopando a lista de escritórios (CLs).
        pagination (PaginacaoMetaDTO): Metadados de controle e navegação da paginação.
    """

    # Configuração do Pydantic v2 para permitir popular atributos via nome ou alias
    model_config = ConfigDict(populate_by_name=True)

    # Objeto contendo os comitês locais e seus roteamentos
    data: DivisaoMercadoCl = Field(..., description="Lista contendo os escritórios e seus respectivos mercados.")

    # Objeto de metadados da paginação
    pagination: PaginacaoMetaDTO = Field(..., description="Metadados de controle da paginação.")


class ListagemEscritoriosRespostaDTOUniversidades(BaseModel):
    """Modelo principal que unifica e valida o payload completo de retorno para Universidades.

    Attributes:
        data (DivisaoMercadoUniversidades): Wrapper envelopando a lista de universidades.
        pagination (PaginacaoMetaDTO): Metadados de controle e navegação da paginação.
    """

    # Configuração do Pydantic v2 para permitir popular atributos via nome ou alias
    model_config = ConfigDict(populate_by_name=True)

    # Objeto contendo as universidades e seus roteamentos
    data: DivisaoMercadoUniversidades = Field(..., description="Lista contendo os escritórios e seus respectivos mercados.")

    # Objeto de metadados da paginação
    pagination: PaginacaoMetaDTO = Field(..., description="Metadados de controle da paginação.")


# =================================================================================
# 5. EXPORTAÇÃO DO MÓDULO
# =================================================================================
__all__ = [
    "DivisaoMercadoCl",
    "DivisaoMercadoUniversidades",
    "ListagemEscritoriosRespostaDTOCL",
    "ListagemEscritoriosRespostaDTOUniversidades",
]