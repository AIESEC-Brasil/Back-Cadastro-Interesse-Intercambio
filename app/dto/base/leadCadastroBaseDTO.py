"""
Módulo Base de Schemas e DTOs para Pré-Cadastro de Leads.

Este módulo define a classe base `LeadPreCadastroBase`, contendo a estrutura
de dados e validações comuns para o fluxo de pré-cadastro na aplicação.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================

# Módulos nativos do Python para suporte a anotações de tipos
from typing import (
    Any,        # Tipo flexível para aceitar qualquer payload de dados brutos do Podio.
    List,       # Hint de tipo para representar listas/arrays de elementos.
    Optional,   # Hint de tipo para indicar campos opcionais que podem receber None.
)

# Importações do Pydantic (versão 2) utilizadas na construção e validação da estrutura de dados
from pydantic import (
    BaseModel,       # Classe base do Pydantic para criação de modelos/containers de dados.
    ConfigDict,      # Objeto de configuração para definir comportamentos do modelo.
    Field,           # Utilizado para definir metadados dos campos, descrições, aliases e exemplos.
    model_validator, # Validador de modelo do Pydantic v2.
)

# Importação dos DTOs e tipos globais customizados da aplicação
from ..globals import (
    Autorizacao,
    Comite,
    DataNascimento,
    EmailItem,
    Meio,
    Origem,
    Produto,
    Tag,
    TelefoneItem,
    Universidade,
)


# =================================================================
# 2. ESTRUTURA DOS MODELOS (SCHEMAS / DTOs)
# =================================================================

class LeadPreCadastroBase(BaseModel):
    """
    Modelo de dados Pydantic para validação e documentação do pré-cadastro de Leads.

    Esta classe define a estrutura base esperada para o payload de pré-cadastro,
    incluindo metadados e exemplos para a geração automatizada de JSON Schema (OpenAPI).

    Regras de negócio:
        - Deve existir pelo menos um dos campos:
            * universidade
            * comite
        - Ambos também podem ser enviados simultaneamente.
    """

    # Configuração global do modelo: ignora campos extras não declarados no payload
    model_config = ConfigDict(extra="ignore")

    # Primeiro nome do lead (obrigatório)
    nome: str = Field(
        description="Nome do lead",
        json_schema_extra={
            "example": "João"
        },
        min_length=3,
        max_length=100,
        pattern=r"^[A-Za-zÀ-ÿ\s]+$",
    )

    # Sobrenome completo do lead (obrigatório)
    sobrenome: str = Field(
        description="Sobrenome do lead",
        json_schema_extra={
            "example": "Silva"
        },
        min_length=3,
        max_length=100,
        pattern=r"^[A-Za-zÀ-ÿ\s]+$",
    )

    # Objeto contendo o dia, mês e ano de nascimento do lead
    dataNascimento: DataNascimento

    # Coleção de telefones informados para contato
    telefone: List[TelefoneItem]

    # Coleção de endereços de e-mail informados para contato
    email: List[EmailItem]

    # Instituição de ensino associada ao lead
    universidade: Optional[Universidade] = Field(
        default=None,
        description="Instituição de ensino vinculada ao lead (opcional)",
    )

    # Produto ou programa de interesse selecionado no fluxo
    produto: Produto

    # Comitê local/regional atribuído para o atendimento do lead
    comite: Optional[Comite] = Field(
        default=None,
        description="Comitê responsável pelo atendimento do lead (opcional)",
    )

    # Termos de aceite e consentimentos legais fornecidos pelo lead
    autorizacao: Autorizacao

    # Origem primária pela qual o lead conheceu a AIESEC
    origem: Origem

    # Meio secundário ou canal específico de contato do lead
    meio: Optional[Meio] = Field(
        default=None,
        description="Meio de contato pelo qual o lead conheceu a AIESEC (opcional)",
    )

    # Coleção de tags de eventos ou campanhas de atração
    tag: Optional[List[Tag]] = Field(
        default=None,
        description="Lista de tags de evento ou campanha utilizadas na atração (opcional)",
    )

    # =============================================================
    # VALIDAÇÕES DE NEGÓCIO
    # =============================================================

    @model_validator(mode="after")
    def validar_universidade_ou_comite(self):
        """
        Garante que pelo menos um dos campos abaixo seja informado:
            - universidade
            - comite

        Ambos podem ser enviados simultaneamente.
        """

        if self.universidade is None and self.comite is None:
            raise ValueError(
                "É obrigatório informar ao menos um dos campos: universidade ou comite."
            )

        return self


# =================================================================
# 3. EXPORTAÇÃO CONSOLIDADA DO MÓDULO
# =================================================================

__all__ = ["LeadPreCadastroBase"]