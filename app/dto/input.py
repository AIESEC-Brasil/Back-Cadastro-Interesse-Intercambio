"""Modelos de entrada usados pelas rotas e serviços."""

from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field, PositiveInt

from .types import (
    AreaAtuacao,
    Idioma,
    LeadPreCadastroBase,
    NivelAtuacao,
    SemestreCurso,
    Senha,
    UploadItem,
)

LeadPreCadastroInput: TypeAlias = LeadPreCadastroBase


class CriarPreCadastroB2C(LeadPreCadastroBase):
    """Entrada do formulário B2C sem senha ou criação de cadastro no EXPA."""

    model_config = ConfigDict(extra="forbid")


class CriarPreCadastroLead(LeadPreCadastroInput):
    """Entrada para criação de lead EXPA, incluindo a senha de acesso."""

    model_config = ConfigDict(extra="forbid")

    senha: Senha


class QualificacaoLead(BaseModel):
    """Dados opcionais de qualificação enviados após o pré-cadastro."""

    model_config = ConfigDict(extra="ignore")

    id: PositiveInt = Field(description="Identificador retornado na primeira etapa")
    curso: str | None = Field(
        default=None,
        max_length=100,
        pattern=r"^[A-Za-zÀ-ÿ\s]+$",
        description="Nome do curso de graduação ou pós-graduação",
    )
    idiomas: list[Idioma] | None = None
    areaAtuacao: AreaAtuacao | None = None
    nivelAtuacao: NivelAtuacao | None = None
    semestreCurso: SemestreCurso | None = None
    id_area_atuacao: PositiveInt | None = None
    id_nivel_mercado: PositiveInt | None = None
    id_semestre_curso: PositiveInt | None = None
    curriculo: UploadItem | None = Field(
        default=None,
        description="Currículo PDF codificado em Base64",
    )


AtualizarPreCadastroLead = QualificacaoLead


__all__ = [
    "AtualizarPreCadastroLead",
    "CriarPreCadastroB2C",
    "CriarPreCadastroLead",
    "LeadPreCadastroInput",
    "QualificacaoLead",
]
