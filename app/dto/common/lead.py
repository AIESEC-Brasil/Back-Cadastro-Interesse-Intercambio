"""Tipos compartilhados pelos payloads de cadastro de leads."""

from datetime import date, datetime
from enum import IntEnum
import re
from typing import Annotated, ClassVar, Self, TypeAlias

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    PositiveInt,
    model_validator,
)


def validar_opcao_cache(external_id: str, id_opcao: int, nome: str) -> None:
    """Confere ID e nome contra as opções ativas de um campo B2C."""
    from app.utils.metadados import buscar_campo_metadado, buscar_opcoes_metadado

    if buscar_campo_metadado(external_id) is None:
        raise ValueError(f"O campo '{external_id}' não foi encontrado nos metadados B2C.")

    for option in buscar_opcoes_metadado(external_id):
        if str(option.get("id")) != str(id_opcao):
            continue
        label: object = option.get("text", option.get("name", ""))
        if isinstance(label, str) and label.strip() == nome.strip():
            return
        raise ValueError("O nome informado não corresponde ao ID selecionado.")

    raise ValueError(f"O ID {id_opcao} não é uma opção ativa do campo '{external_id}'.")


def buscar_id_opcao_cache(external_id: str, valor: str) -> int:
    """Resolve o ID ativo de uma opção do cache a partir do texto recebido."""
    from app.utils.metadados import buscar_campo_metadado, buscar_opcoes_metadado

    if buscar_campo_metadado(external_id) is None:
        raise ValueError(f"O campo '{external_id}' não foi encontrado nos metadados B2C.")

    for option in buscar_opcoes_metadado(external_id):
        texto: object = option.get("text", option.get("name", ""))
        if not isinstance(texto, str):
            continue
        if texto.strip().casefold() == valor.strip().casefold():
            try:
                return int(option["id"])
            except (KeyError, TypeError, ValueError) as erro:
                raise ValueError(
                    f"A opção '{valor}' não possui um ID válido no campo '{external_id}'."
                ) from erro

    raise ValueError(f"O valor '{valor}' não é uma opção ativa do campo '{external_id}'.")


def validar_texto_opcao_cache(external_id: str, valor: str) -> None:
    """Confere texto/valor de uma opção contra as opções ativas do cache B2C."""
    buscar_id_opcao_cache(external_id, valor)


class ReferenciaLead(BaseModel):
    """Referência a uma universidade, comitê, origem ou meio."""

    model_config = ConfigDict(extra="allow")

    external_id: ClassVar[str | None] = None

    id: PositiveInt
    nome: str

    @classmethod
    def validar_opcao_cache(cls, id_opcao: int, nome: str) -> None:
        """Confere ID e nome contra as opções ativas do cache B2C."""
        if cls.external_id is None:
            return
        validar_opcao_cache(cls.external_id, id_opcao, nome)

    @model_validator(mode="after")
    def validar_referencia_ativa(self) -> Self:
        """Valida a referência no cache quando houver um campo associado."""
        self.__class__.validar_opcao_cache(self.id, self.nome)
        return self


class ProdutoLead(BaseModel):
    """Produto escolhido no formulário de interesse."""

    model_config = ConfigDict(extra="ignore")

    titulo: str
    id: PositiveInt
    id_expa: PositiveInt

    @model_validator(mode="after")
    def validar_produto(self) -> Self:
        """Confere o produto no cache e o código EXPA aceito."""
        if self.id_expa not in {7, 8, 9}:
            raise ValueError("ID EXPA inválido; valores aceitos: 7, 8 ou 9.")
        validar_opcao_cache("produto", self.id, self.titulo)
        return self


# Nomes usados pelos DTOs anteriores, mantidos como aliases compatíveis.
Produto = ProdutoLead


class Universidade(ReferenciaLead):
    """Instituição de ensino associada ao lead."""


class Comite(ReferenciaLead):
    """Comitê responsável pelo atendimento do lead."""

    external_id: ClassVar[str] = "aiesec_proxima"


class Origem(ReferenciaLead):
    """Origem pela qual o lead conheceu a organização."""

    external_id: ClassVar[str] = "origem"


class Meio(ReferenciaLead):
    """Canal de contato pelo qual o lead conheceu a organização."""

    external_id: ClassVar[str] = "meio"


class AreaAtuacao(ReferenciaLead):
    """Área de atuação selecionada pelo lead."""

    external_id: ClassVar[str] = "area_atuacao"


class Idioma(ReferenciaLead):
    """Idioma informado pelo lead."""

    external_id: ClassVar[str] = "idiomas"


class NivelAtuacao(ReferenciaLead):
    """Nível de atuação informado pelo lead."""

    external_id: ClassVar[str] = "nivel_mercado"


class SemestreCurso(ReferenciaLead):
    """Semestre atual do curso informado pelo lead."""

    external_id: ClassVar[str] = "semestre_curso"


def _validar_data_nascimento(valor: datetime) -> datetime:
    """Rejeita datas de nascimento futuras."""
    if valor.date() > date.today():
        raise ValueError("A data de nascimento não pode ser uma data futura.")
    return valor


def _validar_tag(valor: str) -> str:
    """Aceita tags minúsculas, sem espaços ou acentos."""
    import unicodedata

    if valor != valor.lower() or any(char.isspace() for char in valor):
        raise ValueError("A tag deve estar em minúsculas e não conter espaços.")
    if any(unicodedata.category(char) == "Mn" for char in unicodedata.normalize("NFD", valor)):
        raise ValueError("A tag não pode conter acentos.")
    return valor


def _validar_senha(valor: str) -> str:
    """Aplica os critérios de segurança usados pelo DTO histórico de senha."""
    regras = (
        (len(valor) >= 8, "A senha deve conter no mínimo 8 caracteres."),
        (not any(char.isspace() for char in valor), "A senha não pode conter espaços."),
        (not any(ord(char) < 32 for char in valor), "A senha contém caracteres de controle."),
        (not any(char in {";", "'", '"', "`", "\\"} for char in valor), "A senha contém caracteres não permitidos."),
        (bool(re.search(r"[a-z]", valor)), "A senha deve conter uma letra minúscula."),
        (bool(re.search(r"[A-Z]", valor)), "A senha deve conter uma letra maiúscula."),
        (bool(re.search(r"\d", valor)), "A senha deve conter um número."),
        (bool(re.search(r"[@$!%*?&]", valor)), "A senha deve conter um caractere especial (@$!%*?&)."),
    )
    falhas = [mensagem for valida, mensagem in regras if not valida]
    if falhas:
        raise ValueError(" ".join(falhas))
    return valor


DataNascimento: TypeAlias = Annotated[datetime, AfterValidator(_validar_data_nascimento)]
Tag: TypeAlias = Annotated[str, AfterValidator(_validar_tag)]
Senha: TypeAlias = Annotated[
    str,
    Field(min_length=8, max_length=128, description="Senha de acesso do lead"),
    AfterValidator(_validar_senha),
]


class Autorizacao(IntEnum):
    """Valores numéricos de consentimento aceitos no payload."""

    SIM = 1
    NAO = 2


__all__ = [
    "AreaAtuacao",
    "Autorizacao",
    "Comite",
    "DataNascimento",
    "Idioma",
    "Meio",
    "NivelAtuacao",
    "Origem",
    "ProdutoLead",
    "Produto",
    "ReferenciaLead",
    "Senha",
    "SemestreCurso",
    "Tag",
    "Universidade",
    "validar_opcao_cache",
    "buscar_id_opcao_cache",
    "validar_texto_opcao_cache",
]
