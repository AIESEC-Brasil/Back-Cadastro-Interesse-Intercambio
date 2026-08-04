"""Módulo de Schemas e DTOs para Entidades Universitárias.

Este módulo define a estrutura Pydantic utilizada para representar a Universidade.
Por se tratar de um objeto opcional, todos os seus campos possuem valores padrão
nulos (`default=None`), permitindo payloads parciais ou vazios.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from typing import Optional  # Suporte a tipagem estática para valores que podem ser Nulos (None)

from pydantic import (
    BaseModel,   # Classe base para criação de modelos de dados com validação automática.
    ConfigDict,  # Objeto de configuração para definir comportamentos do modelo (ex: permitir aliases, proibir campos extras).
    Field,       # Utilizado para definir metadados dos campos, como descrições, aliases e exemplos para o JSON Schema.
    PositiveInt,      # Tipa e valida se o número é um inteiro positivo (> 0).
)


# =================================================================
# 2. MODELOS DE DADOS (SCHEMAS)
# =================================================================

class Universidade(BaseModel):
    """Representa a entidade opcional de dados de uma Universidade.

    Esta classe abstrai as propriedades de identificação da universidade.
    Todos os campos possuem `default=None`, tornando o preenchimento da classe
    totalmente opcional no modelo e na visão geral.

    Attributes:
        id (Optional[int]): Identificador da universidade no banco de dados. Padrão: None.
        nome (Optional[str]): Nome oficial da universidade. Padrão: None.
    """

    # Identificador único da universidade no banco de dados (Opcional)
    id: PositiveInt = Field(
        description="Id da Universidade no Banco de Dados",
        json_schema_extra={"example": 1},
    )

    # Nome completo da universidade no banco de dados (Opcional)
    nome: str = Field(
        description="Nome da Universidade no Banco de Dados",
        json_schema_extra={"example": "Universidade Federal de Pernambuco"},
    )

    # Configuração global do Pydantic para ignorar atributos não declarados no payload de entrada
    model_config = ConfigDict(extra="ignore")


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["Universidade"]