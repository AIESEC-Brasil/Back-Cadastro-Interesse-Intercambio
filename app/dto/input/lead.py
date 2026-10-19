"""DTOs de entrada para pré-cadastro e criação de leads."""

from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field, PositiveInt

from ..base import LeadPreCadastroBase
from ..common import AreaAtuacao, Idioma, NivelAtuacao, Senha, SemestreCurso
from .upload import UploadItem

LeadPreCadastroInput: TypeAlias = LeadPreCadastroBase


class CriarPreCadastroLead(LeadPreCadastroInput):
    """Payload de criação de lead, incluindo a senha de acesso."""

    model_config = ConfigDict(extra="forbid")

    senha: Senha


class QualificacaoLead(BaseModel):
    """Payload da segunda etapa do cadastro, com dados de qualificação do lead."""

    model_config = ConfigDict(extra="ignore")

    id: PositiveInt = Field(description="Identificador do cadastro criado na primeira etapa")
    curso: str | None = Field(
        default=None,
        max_length=100,
        pattern=r"^[A-Za-zÀ-ÿ\s]+$",
        description="Nome do curso de graduação ou pós-graduação",
    )
    idiomas: list[Idioma] | None = Field(
        default=None,
        description="Idiomas e níveis de fluência informados pelo lead",
    )
    areaAtuacao: AreaAtuacao | None = Field(
        default=None,
        description="Área de atuação profissional ou acadêmica",
    )
    nivelAtuacao: NivelAtuacao | None = Field(
        default=None,
        description="Nível de experiência ou senioridade",
    )
    semestreCurso: SemestreCurso | None = Field(
        default=None,
        description="Semestre atual do curso",
    )
    curriculo: UploadItem | None = Field(
        default=None,
        description="Currículo PDF codificado em Base64",
    )


# Alias compatível com o nome já usado pelo controller.
AtualizarPreCadastroLead = QualificacaoLead


__all__ = [
    "LeadPreCadastroInput",
    "CriarPreCadastroLead",
    "QualificacaoLead",
    "AtualizarPreCadastroLead",
]
