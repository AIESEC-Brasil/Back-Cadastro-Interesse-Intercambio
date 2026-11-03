"""Modelos de saída e payloads enviados às integrações externas."""

from datetime import datetime
from enum import IntEnum
from typing import Any, Generic, Literal, Self, TypeVar
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

from .types import (
    Autorizacao,
    DataNascimento,
    LeadPreCadastroBase,
    Tag,
    UploadItem,
)


class HttpStatus(IntEnum):
    """Códigos HTTP usados pela API e pelos serviços integrados."""

    OK = 200
    CREATED = 201
    MOVED_PERMANENTLY = 301
    FOUND = 302
    PERMANENT_REDIRECT = 308
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    REQUEST_TIMEOUT = 408
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504


def _formatar_timestamp_pt_br(valor: datetime | str) -> str:
    """Formata data/hora de metadados para o padrão legível da API."""
    if isinstance(valor, str):
        return valor
    data_hora = valor.astimezone(ZoneInfo("America/Sao_Paulo"))
    dias = (
        "segunda-feira",
        "terça-feira",
        "quarta-feira",
        "quinta-feira",
        "sexta-feira",
        "sábado",
        "domingo",
    )
    meses = (
        "janeiro",
        "fevereiro",
        "março",
        "abril",
        "maio",
        "junho",
        "julho",
        "agosto",
        "setembro",
        "outubro",
        "novembro",
        "dezembro",
    )
    return (
        f"{dias[data_hora.weekday()].capitalize()}, {data_hora.day:02d} de "
        f"{meses[data_hora.month - 1].capitalize()} de {data_hora.year}, "
        f"{data_hora:%H:%M:%S}"
    )


class ConfiguracoesCampo(BaseModel):
    """Configurações e opções de um campo de metadados."""

    model_config = ConfigDict(extra="allow")
    description: str | None = None
    options: list[dict[str, Any]] = Field(default_factory=list)


class ConfiguracaoMetadado(BaseModel):
    """Configurações do campo retornado pelos metadados B2C."""

    model_config = ConfigDict(extra="allow")
    settings: ConfiguracoesCampo


class CampoMetadado(BaseModel):
    """Campo de metadado retornado pelo Apps Script B2C."""

    model_config = ConfigDict(extra="allow")
    external_id: str
    config: ConfiguracaoMetadado


class DadosMetadados(BaseModel):
    """Campos e categorias de contato disponíveis no formulário."""

    fields: list[CampoMetadado]
    categorias_contato: dict[str, list[str]]


class Metadados(BaseModel):
    """Metadados B2C e horário da última atualização."""

    data: DadosMetadados
    timestamp: datetime | str = Field(
        description="Data e hora em que os metadados foram atualizados no cache"
    )

    @field_serializer("timestamp")
    def formatar_timestamp(self: Self, valor: datetime | str) -> str:
        """Serializa o timestamp no formato legível usado pelo formulário."""
        return _formatar_timestamp_pt_br(valor)


class DivisaoMercadoMetadados(BaseModel):
    """Resposta de escritórios ou universidades com seus dados originais."""

    model_config = ConfigDict(extra="allow")

    recurso: str
    path: str
    aba: str
    total: int
    dados: list[dict[str, Any]]
    timestamp: datetime | str = Field(
        description="Data e hora em que os metadados foram atualizados no cache"
    )

    @field_serializer("timestamp")
    def formatar_timestamp(self: Self, valor: datetime | str) -> str:
        """Serializa o timestamp no formato legível usado pela API."""
        return _formatar_timestamp_pt_br(valor)


T = TypeVar("T")


class RetornoGenerico(BaseModel, Generic[T]):
    """Envelope genérico de resposta com sucesso e dados opcionais."""

    model_config = ConfigDict(extra="ignore")
    sucesso: bool = Field(default=True, description="Indica se a operação teve sucesso")
    data: T | None = Field(default=None, description="Dados da resposta")


class ConflitoEmail(BaseModel):
    """E-mail que já existe no cadastro."""

    email: EmailStr = Field(description="E-mail em conflito")


class ConflitoTelefone(BaseModel):
    """Telefone que já existe no cadastro."""

    numero: str = Field(description="Telefone em conflito")


class ConflitosLeadOutput(BaseModel):
    """E-mails e telefones encontrados em conflito."""

    model_config = ConfigDict(extra="forbid")
    emails: list[ConflitoEmail] | None = None
    telefone: list[ConflitoTelefone] | None = None


class TelefonePersistencia(BaseModel):
    """Telefone com ID de categoria para persistência."""

    model_config = ConfigDict(extra="allow")
    tipo: PositiveInt
    numero: str


class EmailPersistencia(BaseModel):
    """E-mail com ID de categoria para persistência."""

    model_config = ConfigDict(extra="allow")
    tipo: PositiveInt
    email: EmailStr


class LeadPersistencia(BaseModel):
    """Dados do lead devolvidos após criação no EXPA."""

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
        """Aceita os formatos históricos e ISO de data/hora."""
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
        """Serializa a criação no formato usado pelo Apps Script."""
        return valor.strftime("%d/%m/%Y %H:%M:%S")


class LeadPreCadastroB2CPersistencia(BaseModel):
    """Dados reduzidos enviados ao B2C no cadastro direto."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["pré-cadastro b2c"] = "pré-cadastro b2c"
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
    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo("America/Sao_Paulo"))
    )
    tag: list[Tag] | None = None

    @field_validator("criado_em", mode="before")
    @classmethod
    def validar_criado_em(cls, valor: Any) -> datetime:
        """Aceita os formatos históricos e ISO de data/hora."""
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
        """Serializa a criação no formato usado pelo Apps Script."""
        return valor.strftime("%d/%m/%Y %H:%M:%S")


class QualificacaoPersistencia(BaseModel):
    """Dados da qualificação no formato aceito pela persistência."""

    model_config = ConfigDict(extra="forbid")

    id: PositiveInt
    status: Literal["qualificação"] = "qualificação"
    curso: str | None = None
    idiomas: list[PositiveInt] | None = None
    id_area_atuacao: PositiveInt | None = None
    id_nivel_mercado: PositiveInt | None = None
    id_semestre_curso: PositiveInt | None = None
    curriculo: UploadItem | None = None


class PayloadExpa(BaseModel):
    """Payload plano enviado ao Apps Script de integração EXPA."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    nome: str
    sobrenome: str
    senha: str
    data_nascimento: str = Field(serialization_alias="dataNascimento")
    programa: PositiveInt
    nome_cl: str = Field(serialization_alias="nomeCL")
    telefone: str
    email: str
    token_expa: str = Field(
        min_length=1,
        repr=False,
        serialization_alias="tokenExpa",
    )


class LeadPreCadastroOutput(LeadPreCadastroBase):
    """Cadastro criado no EXPA, identificado pelo ID retornado."""

    model_config = ConfigDict(extra="forbid")
    id: PositiveInt = Field(description="Identificador do lead")


class LeadPreCadastroB2COutput(LeadPreCadastroB2CPersistencia):
    """Payload reduzido devolvido após o pré-cadastro B2C."""


__all__ = [
    "CampoMetadado",
    "ConfiguracaoMetadado",
    "ConfiguracoesCampo",
    "ConflitoEmail",
    "ConflitoTelefone",
    "ConflitosLeadOutput",
    "DadosMetadados",
    "DivisaoMercadoMetadados",
    "EmailPersistencia",
    "HttpStatus",
    "LeadPersistencia",
    "LeadPreCadastroB2COutput",
    "LeadPreCadastroB2CPersistencia",
    "LeadPreCadastroOutput",
    "Metadados",
    "PayloadExpa",
    "QualificacaoPersistencia",
    "RetornoGenerico",
    "TelefonePersistencia",
]
