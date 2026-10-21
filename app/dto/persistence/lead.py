"""DTO de persistência do cadastro de leads."""

from datetime import datetime
from typing import Literal
from typing import Self
from zoneinfo import ZoneInfo

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    PositiveInt,
    field_serializer,
)

from ..types import DataNascimento, Tag, UploadItem


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
    universidade: str | None = None
    dataNascimento: DataNascimento
    id_nivel_mercado: PositiveInt | None = None
    id_area_atuacao: PositiveInt | None = None
    id_meio: PositiveInt | None = None
    id_semestre_curso: PositiveInt | None = None
    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo("America/Sao_Paulo"))
    )
    link_drive: UploadItem | None = None
    tag: list[Tag] | None = None

    @field_serializer("criado_em")
    def serializar_criado_em(self: Self, valor: datetime) -> str:
        """Serializa a data no formato dia/mês/ano hora:minuto:segundo."""
        return valor.strftime("%d/%m/%Y %H:%M:%S")


__all__ = ["EmailPersistencia", "LeadPersistencia", "TelefonePersistencia"]
