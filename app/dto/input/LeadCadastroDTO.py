from pydantic import (
    BaseModel,       # Classe base do Pydantic para criação de modelos/containers de dados.
    Field,           # Utilizado para definir metadados dos campos, descrições, aliases e exemplos para o JSON Schema.
    ConfigDict,      # Objeto de configuração para definir comportamentos do modelo (ex: permitir aliases, proibir campos extras).
)

from typing import (
    List,            # Hint de tipo para representar listas/arrays de elementos.
    Any,             # Tipo flexível para aceitar qualquer payload de dados brutos do Podio.
    Optional         # Hint de tipo para indicar campos opcionais que podem receber None.
)

# Importação dos tipos/modelos globais customizados da aplicação
from ..globals import Comite, EmailItem, Autorizacao, TelefoneItem, DataNascimento, Produto,Universidade

class LeadPreCadastroInput(BaseModel):
    """
    Modelo de dados Pydantic para validação e documentação do pré-cadastro de Leads.

    Esta classe define a estrutura esperada para o payload de pré-cadastro,
    incluindo metadados e exemplos para a geração automatizada de JSON Schema (OpenAPI).

    Attributes:
        nome (str): Primeiro nome do lead.
        sobrenome (str): Sobrenome completo do lead.
        senha (str): Senha de acesso escolhida pelo usuário.
        dataNascimento (DataNascimento): Objeto com os dados de nascimento validados.
        telefone (List[TelefoneItem]): Lista de telefones de contato do lead.
        email (List[EmailItem]): Lista de e-mails de contato do lead.
        universidade (Optional[str]): Instituição de ensino vinculada (opcional).
        produto (Produto): Produto/programa de interesse selecionado pelo lead.
        comite (Comite): Comitê local responsável pelo atendimento do lead.
        autorizacao (Autorizacao): Consentimentos e autorizações de termos do lead.
    """
    model_config = ConfigDict(extra='forbid')
    nome: str = Field(
        description="Nome do lead",
        json_schema_extra={
            "example": "João"  # Corrigido para 'example' para seguir o padrão OpenAPI moderno
        }
    )

    sobrenome: str = Field(
        description="Sobrenome do lead",
        json_schema_extra={
            "example": "Silva"
        }
    )

    # Objetos complexos validados por sub-modelos importados do globals
    dataNascimento: DataNascimento
    telefone: List[TelefoneItem]
    email: List[EmailItem]

    # Campo opcional com valor padrão e metadados corrigidos
    universidade: Optional[Universidade] = Field(
        default=None,
        description="Universidade ou instituição de ensino do lead"
    )

    # Demais campos obrigatórios da regra de negócio
    produto: Produto
    comite: Comite
    autorizacao: Autorizacao

class CriarPreCadastroLead(LeadPreCadastroInput):
    model_config = ConfigDict(extra='forbid')
    senha: str = Field(
        description="Senha de acesso do lead",
        json_schema_extra={
            "example": "teste123"
        }
    )


# Define os elementos exportados publicamente ao utilizar 'from modulo import *'
__all__ = ["LeadPreCadastroInput","CriarPreCadastroLead"]