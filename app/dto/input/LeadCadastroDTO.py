"""Módulo de Schemas e DTOs para Pré-Cadastro de Leads.

Este módulo define a estrutura de dados (Data Transfer Objects) utilizada para
receber, validar e documentar os payloads de pré-cadastro de leads na aplicação.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from typing import (
    Any,       # Tipo flexível para aceitar qualquer payload de dados brutos do Podio.
    List,      # Hint de tipo para representar listas/arrays de elementos.
    Optional,  # Hint de tipo para indicar campos opcionais que podem receber None.
)

from pydantic import (
    BaseModel,   # Classe base do Pydantic para criação de modelos/containers de dados.
    ConfigDict,  # Objeto de configuração para definir comportamentos do modelo.
    Field,       # Utilizado para definir metadados dos campos, descrições, aliases e exemplos.
)

# Importação dos tipos/modelos globais customizados da aplicação
from ..globals import (
    Autorizacao,
    Comite,
    DataNascimento,
    EmailItem,
    Produto,
    TelefoneItem,
    Universidade,
)


# =================================================================
# 2. MODELOS DE DADOS (SCHEMAS)
# =================================================================

class LeadPreCadastroInput(BaseModel):
    """Modelo de dados Pydantic para validação e documentação do pré-cadastro de Leads.

    Esta classe define a estrutura base esperada para o payload de pré-cadastro,
    incluindo metadados e exemplos para a geração automatizada de JSON Schema (OpenAPI).

    Attributes:
        nome (str): Primeiro nome do lead.
        sobrenome (str): Sobrenome completo do lead.
        dataNascimento (DataNascimento): Objeto com os dados de nascimento validados.
        telefone (List[TelefoneItem]): Lista de telefones de contato do lead.
        email (List[EmailItem]): Lista de e-mails de contato do lead.
        universidade (Optional[Universidade]): Instituição de ensino vinculada (opcional). Padrão: None.
        produto (Produto): Produto/programa de interesse selecionado pelo lead.
        comite (Comite): Comitê local responsável pelo atendimento do lead.
        autorizacao (Autorizacao): Consentimentos e autorizações de termos do lead.
    """

    # Configuração global do modelo: ignora campos extras não declarados no payload
    model_config = ConfigDict(extra="ignore")

    # Primeiro nome do lead (obrigatório)
    nome: str = Field(
        description="Nome do lead",
        json_schema_extra={
            "example": "João"  # Exemplo exibido na documentação interativa (Swagger/OpenAPI)
        },
    )

    # Sobrenome completo do lead (obrigatório)
    sobrenome: str = Field(
        description="Sobrenome do lead",
        json_schema_extra={
            "example": "Silva"
        },
    )

    # Objeto contendo o dia, mês e ano de nascimento do lead (validado pelo schema DataNascimento)
    dataNascimento: DataNascimento

    # Coleção de telefones informados para contato (validada pelo sub-modelo TelefoneItem)
    telefone: List[TelefoneItem]

    # Coleção de endereços de e-mail informados para contato (validada pelo sub-modelo EmailItem)
    email: List[EmailItem]

    # Instituição de ensino associada ao lead (campo totalmente opcional; assume None se omitido)
    universidade: Optional[Universidade] = Field(
        default=None,
        description="Instituição de ensino vinculada ao lead (opcional)",
    )

    # Produto ou programa de interesse selecionado no fluxo (validado pelo schema Produto)
    produto: Produto

    # Comitê local/regional atribuído para o atendimento do lead (validado pelo schema Comite)
    comite: Comite

    # Termos de aceite e consentimentos legais fornecidos pelo lead (validados pelo schema Autorizacao)
    autorizacao: Autorizacao


class CriarPreCadastroLead(LeadPreCadastroInput):
    """Modelo estendido para criação de pré-cadastro de Lead contendo credenciais.

    Herda todos os atributos e validações de `LeadPreCadastroInput` e adiciona
    a obrigatoriedade da senha de acesso. Aplica uma política estrita (`extra='forbid'`)
    onde qualquer campo não especificado no payload resultará em erro de validação.

    Attributes:
        senha (str): Senha de acesso escolhida pelo usuário para autenticação.
    """

    # Configuração estrita: proíbe explicitamente qualquer campo extra não especificado
    model_config = ConfigDict(extra="forbid")

    # Credencial/Senha criada pelo lead para autenticação no sistema (obrigatória no cadastro)
    senha: str = Field(
        description="Senha de acesso do lead",
        json_schema_extra={
            "example": "teste123"
        },
    )


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["LeadPreCadastroInput", "CriarPreCadastroLead"]