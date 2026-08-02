"""Módulo de Submodelos de Apoio para DTOs (Data Transfer Objects).

Este arquivo define estruturas de dados compartilhadas que compõem múltiplos
objetos de transferência de dados no sistema, garantindo validação rigorosa
e formatação amigável para integração com APIs (ex: Podio) e interfaces de usuário.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from typing import (
    Any,   # Permite tipagem flexível em entradas dinâmicas antes da validação
    List   # Define tipagem para listas e coleções de elementos no TypeAdapter
)

from pydantic import (
    BaseModel,    # Classe base para criação de modelos com validação automática
    ConfigDict,   # Configurações globais do modelo Pydantic v2 (ex: aliases)
    Field,        # Define metadados dos campos (descrições, exemplos e aliases)
    TypeAdapter,  # Permite validação e conversão de coleções complexas/listas
    PositiveInt   # Tipa e valida se é inteiro e positivo
)


# =================================================================
# 2. SUB-MODELOS DE APOIO (DTOs)
# =================================================================
class DivisaoMercado(BaseModel):
    """Estrutura para representar o mapeamento e divisão de mercado por Comitê Local ou Instituição de Ensino.

    Utiliza aliases customizados para realizar o parse direto de chaves que contêm caracteres especiais e espaços
    vindas de payloads externos estruturados (Ex: dicionários estruturados com a chave 'Voluntario Global').

    Attributes:
        id (int): Identificador interno sequencial da linha de divisão.
        nome (str): Nome amigável da divisão de captação (Ex: nome da universidade ou CL parceiro).
        gv (str): Nome da unidade responsável pelo roteamento de leads do programa Voluntariado Global.
        gt (str): Nome da unidade responsável pelo roteamento de leads do programa Talentos Globais.
        model_config (ConfigDict): Configuração do Pydantic que habilita 'populate_by_name'.
    """

    id: PositiveInt = Field(
        description="ID interno numérico da divisão de mercado",
        json_schema_extra={"example": 1}
    )
    nome: str = Field(
        description="Nome amigável da divisão (CL ou Instituição vinculada)",
        json_schema_extra={"example": "Recife(PE)"}
    )
    gv: str = Field(
        alias="Voluntario Global",  # Vincula a chave descritiva com espaços ao atributo compacto do Python
        description="Destino de routing para leads de Voluntariado Global",
        json_schema_extra={"example": "AIESEC em Recife"}
    )
    gt: str = Field(
        alias="Talento Global",     # Vincula a chave descritiva com espaços ao atributo compacto do Python
        description="Destino de routing para leads de Talentos Globais",
        json_schema_extra={"example": "AIESEC em Recife"}
    )

    # Configuração global: populate_by_name=True permite preencher o modelo tanto
    # passando o nome do atributo ('gv') quanto o alias ('Voluntario Global').
    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def processar_lista(cls, dados: Any) -> list:
        """Método de processamento dinâmico em lote para listas de dados de divisão de mercado.

        Instancia um adaptador de tipo dedicado para converter coleções, valida os dados e executa
        o dump convertendo as propriedades de volta para o formato esperado com aliases (chaves com espaços).

        Args:
            dados (Any): Coleção/Lista de dicionários contendo os dados brutos de mercado.

        Returns:
            list: Lista de dicionários reestruturada e serializada com os aliases oficiais aplicados.

        Raises:
            pydantic.ValidationError: Se a coleção fornecida não for compatível com a estrutura do modelo.
        """
        # Cria em tempo de execução um adaptador especializado baseado no contexto dinâmico da classe (cls)
        adapter = TypeAdapter(List[cls])

        # Realiza a validação contra os esquemas da classe e exporta o JSON forçando o uso das chaves com aliases nativos
        return adapter.dump_python(adapter.validate_python(dados), by_alias=True)


# =================================================================
# 3. EXPORTAÇÕES DO MÓDULO
# =================================================================
# Define de forma estrita quais símbolos serão exportados ao utilizar padrões globais como 'from ... import *'
__all__ = [
    "DivisaoMercado",
]