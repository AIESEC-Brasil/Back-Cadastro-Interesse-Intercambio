"""
Módulo de Schemas e DTOs para Pré-Cadastro e Qualificação de Leads.

Este módulo define a estrutura de dados (Data Transfer Objects) utilizada para
receber, validar e documentar os payloads de pré-cadastro e qualificação de leads na aplicação.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================

# Módulos nativos do Python para suporte a anotações de tipos
from typing import (
    List,       # Hint de tipo para representar listas/arrays de elementos.
    Optional,   # Hint de tipo para indicar campos opcionais que podem receber None.
)

# Importações do Pydantic (versão 2) utilizadas na construção e validação da estrutura de dados
from pydantic import (
    ConfigDict,  # Objeto de configuração para definir comportamentos do modelo.
    Field,       # Utilizado para definir metadados dos campos, descrições, aliases e exemplos.
)

# Importação dos DTOs e tipos globais customizados da aplicação
from ..globals import (
    AreaAtuacao,
    Idioma,
    NivelAtuacao,
    SemestreCurso,
    Senha,
    UploadItem,
)

# Importação da classe base do pré-cadastro de leads
from ..base import LeadPreCadastroBase as LeadPreCadastroInput

# Importação do modelo de output do pré-cadastro do lead
from ..output import LeadPreCadastroOutput


# =================================================================
# 2. ESTRUTURA DOS MODELOS (SCHEMAS / DTOs)
# =================================================================

class CriarPreCadastroLead(LeadPreCadastroInput):
    """
    Modelo estendido para criação de pré-cadastro de Lead contendo credenciais.

    Herda todos os atributos e validações de `LeadPreCadastroInput` e adiciona
    a obrigatoriedade da senha de acesso. Aplica uma política estrita (`extra='forbid'`)
    onde qualquer campo não especificado no payload resultará em erro de validação.

    Attributes:
        senha (Senha): Senha de acesso escolhida pelo usuário para autenticação no EXPA.
    """

    # Configuração estrita: proíbe explicitamente qualquer campo extra não especificado
    model_config = ConfigDict(extra="forbid")

    # Credencial/Senha criada pelo lead para autenticação no sistema (obrigatória no cadastro)
    senha: Senha = Field(
        description="Senha de acesso do lead no EXPA",
        json_schema_extra={
            "example": "teste123"
        },
        min_length=8,
        max_length=128
    )


class QualificacaoLead(LeadPreCadastroOutput):
    """
    Modelo de dados Pydantic para qualificação complementar do Lead.

    Herda as propriedades de retorno de `LeadPreCadastroOutput` e estende o perfil do lead
    com informações acadêmicas, profissionais e documentos. Todos os campos nesta etapa
    são estritamente opcionais para permitir o preenchimento gradual.

    Attributes:
        curso (Optional[str]): Nome do curso de graduação ou pós-graduação do lead.
        idiomas (Optional[List[Idioma]]): Lista de idiomas e níveis de fluência do lead.
        areaAtuacao (Optional[AreaAtuacao]): Área de atuação profissional ou acadêmica do lead.
        nivelAtuacao (Optional[NivelAtuacao]): Nível de experiência ou senioridade profissional.
        semestreCurso (Optional[SemestreCurso]): Semestre atual do curso em andamento.
        curriculo (Optional[UploadItem]): Arquivo de currículo enviado em formato PDF (Base64).
    """

    # Configuração global do modelo: ignora campos extras não declarados no payload
    model_config = ConfigDict(extra="ignore")

    # Nome descritivo do curso (opcional; assume None se omitido)
    curso: Optional[str] = Field(
        default=None,
        description="Nome do curso de graduação ou pós-graduação do lead (opcional)",
        json_schema_extra={
            "example": "Gestão da Informação"  # Exemplo exibido na documentação interativa (Swagger/OpenAPI)
        },
        max_length=100,
        pattern=r"^[A-Za-zÀ-ÿ\s]+$"
    )

    # Coleção de idiomas informados com nível de fluência (opcional; assume None se omitido)
    idiomas: Optional[List[Idioma]] = Field(
        default=None,
        description="Lista de idiomas e níveis de fluência do lead (opcional)"
    )

    # Área de atuação profissional/acadêmica (opcional; validada pelo DTO AreaAtuacao)
    areaAtuacao: Optional[AreaAtuacao] = Field(
        default=None,
        description="Estrutura de área de atuação do lead (opcional)"
    )

    # Nível de experiência/senioridade (opcional; validado pelo DTO NivelAtuacao)
    nivelAtuacao: Optional[NivelAtuacao] = Field(
        default=None,
        description="Estrutura de nível de atuação profissional do lead (opcional)"
    )

    # Semestre atual do curso (opcional; validado pelo DTO SemestreCurso)
    semestreCurso: Optional[SemestreCurso] = Field(
        default=None,
        description="Estrutura do semestre atual do curso do lead (opcional)"
    )

    # Arquivo PDF de currículo enviado via Base64 (opcional; validado pelo DTO UploadItem)
    curriculo: Optional[UploadItem] = Field(
        default=None,
        description="Arquivo PDF do currículo do lead validados via Base64 (opcional)"
    )


# =================================================================
# 3. EXPORTAÇÃO CONSOLIDADA DO MÓDULO
# =================================================================

__all__ = [
    "LeadPreCadastroInput",
    "CriarPreCadastroLead",
    "QualificacaoLead",
]