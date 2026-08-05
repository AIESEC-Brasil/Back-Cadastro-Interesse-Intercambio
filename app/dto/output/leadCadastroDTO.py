"""Módulo de Schemas e DTOs de Saída para Pré-Cadastro de Leads.

Este módulo define a estrutura de dados de resposta (Output DTO) retornada após
o processamento do pré-cadastro de um lead, estendendo o modelo de entrada e
adicionando os dados de identificação gerados pelo Podio.
"""
from types import CoroutineType
# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from pydantic import (
    ConfigDict,  # Configurações globais do modelo Pydantic v2 (ex: permitir aliases, definir comportamento de campos extras).
    Field,  # Utilizado para definir metadados dos campos, descrições, aliases e exemplos para o JSON Schema.
)
# Importação do modelo base de transferência de dados de entrada de pré-cadastro
from ..input import LeadPreCadastroInput

# =================================================================
# 2. MODELOS DE DADOS DE SAÍDA (OUTPUT SCHEMAS)
# =================================================================

class LeadPreCadastroOutput(LeadPreCadastroInput):
    """Modelo de dados Pydantic para retorno dos dados do pré-cadastro de Lead.

    Estende `LeadPreCadastroInput` para herdar todos os campos enviados na requisição
    de entrada e inclui o `item_id` gerado após a criação do card do Lead na plataforma Podio.

    Attributes:
        item_id (int): Identificador único do card do Lead criado no Podio.
    """

    # Configuração global do modelo: ignora campos extras não mapeados no payload
    model_config = ConfigDict(extra="ignore")

    # Identificador único numérico (ID do item/card) retornado pela API do Podio
    item_id: int = Field(
        ...,
        description="O id do card do Lead no podio",
        json_schema_extra={"example": "325664"},
    )

# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["LeadPreCadastroOutput","LeadOuErroResponse"]
