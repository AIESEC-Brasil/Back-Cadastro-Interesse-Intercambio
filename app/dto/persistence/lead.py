"""DTO de persistência do cadastro de leads."""

from datetime import datetime
from typing import Any, Literal
from typing import Self
from zoneinfo import ZoneInfo

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    PositiveInt,
    field_serializer,
    field_validator,
)

from ..types import (
    Autorizacao,
    DataNascimento,
    Tag,
    UploadItem,
)


# ==============================================================================
# CONTATOS NORMALIZADOS
# ==============================================================================
class TelefonePersistencia(BaseModel):
    """Telefone com o ID persistido para sua categoria."""

    model_config = ConfigDict(extra="allow")

    tipo: PositiveInt
    numero: str


class EmailPersistencia(BaseModel):
    """E-mail com o ID persistido para sua categoria."""

    model_config = ConfigDict(extra="allow")

    tipo: PositiveInt
    email: EmailStr


# ==============================================================================
# PAYLOAD DE PERSISTÊNCIA DO LEAD
# ==============================================================================
class LeadPersistencia(BaseModel):
    """Campos do lead e referências necessários para persistência."""

    model_config = ConfigDict(extra="forbid")

    id: PositiveInt
    status: Literal["pré-cadastro"] = "pré-cadastro"
    id_produto: PositiveInt
    id_status: PositiveInt = 1
    id_escritorio: PositiveInt
    id_origem: PositiveInt
    nome: str
    sobrenome: str
    telefone: list[TelefonePersistencia]
    email: list[EmailPersistencia]
    autorizacao: Autorizacao
    universidade: str | None = None
    dataNascimento: DataNascimento
    id_meio: PositiveInt | None = None
    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo("America/Sao_Paulo"))
    )
    tag: list[Tag] | None = None

    @field_validator("criado_em", mode="before")
    @classmethod
    def validar_criado_em(cls, valor: Any) -> datetime:
        """Aceita o formato de data usado no payload enviado ao Apps Script."""
        if isinstance(valor, datetime):
            return valor
        if isinstance(valor, str):
            try:
                return datetime.strptime(valor, "%d/%m/%Y %H:%M:%S")
            except ValueError:
                try:
                    return datetime.fromisoformat(valor)
                except ValueError as error:
                    raise ValueError("Formato inválido para criado_em.") from error
        raise ValueError("criado_em deve ser uma data ou texto de data válido.")

    @field_serializer("criado_em")
    def serializar_criado_em(self: Self, valor: datetime) -> str:
        """Serializa a data no formato dia/mês/ano hora:minuto:segundo."""
        return valor.strftime("%d/%m/%Y %H:%M:%S")


class QualificacaoPersistencia(BaseModel):
    """Campos da segunda etapa no formato esperado pela persistência."""

    model_config = ConfigDict(extra="forbid")

    id: PositiveInt
    status: Literal["qualificação"] = "qualificação"
    curso: str | None = None
    idiomas: list[PositiveInt] | None = None
    id_area_atuacao: PositiveInt | None = None
    id_nivel_mercado: PositiveInt | None = None
    id_semestre_curso: PositiveInt | None = None
    curriculo: UploadItem | None = None


__all__ = [
    "EmailPersistencia",
    "LeadPersistencia",
    "QualificacaoPersistencia",
    "TelefonePersistencia",
]
