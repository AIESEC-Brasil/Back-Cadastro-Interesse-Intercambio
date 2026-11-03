"""Tipos e modelos compartilhados pelos contratos da aplicação."""

import re
import unicodedata
from datetime import date, datetime
from enum import Enum, IntEnum
from typing import Annotated, ClassVar, Self, TypeAlias

from pydantic import (
    AfterValidator,
    Base64Bytes,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    PositiveInt,
    field_validator,
    model_validator,
)


def validar_opcao_cache(external_id: str, id_opcao: int, nome: str) -> None:
    """Confere ID e nome contra as opções ativas de um campo B2C."""
    from app.utils.metadados import buscar_campo_metadado, buscar_opcoes_metadado

    if buscar_campo_metadado(external_id) is None:
        raise ValueError(
            f"O campo '{external_id}' não foi encontrado nos metadados B2C."
        )

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
        raise ValueError(
            f"O campo '{external_id}' não foi encontrado nos metadados B2C."
        )

    for option in buscar_opcoes_metadado(external_id):
        texto: object = option.get("text", option.get("name", ""))
        if (
            not isinstance(texto, str)
            or texto.strip().casefold() != valor.strip().casefold()
        ):
            continue
        try:
            return int(option["id"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"A opção '{valor}' não possui um ID válido no campo '{external_id}'."
            ) from error

    raise ValueError(
        f"O valor '{valor}' não é uma opção ativa do campo '{external_id}'."
    )


def validar_texto_opcao_cache(external_id: str, valor: str) -> None:
    """Confere o texto da opção contra as opções ativas do cache B2C."""
    buscar_id_opcao_cache(external_id, valor)


class ReferenciaLead(BaseModel):
    """Referência validada a uma opção de metadados."""

    model_config = ConfigDict(extra="allow")
    external_id: ClassVar[str | None] = None

    id: PositiveInt
    nome: str

    @classmethod
    def validar_opcao_cache(cls: type[Self], id_opcao: int, nome: str) -> None:
        """Valida o par ID/nome contra os metadados associados ao subtipo."""
        if cls.external_id is not None:
            validar_opcao_cache(cls.external_id, id_opcao, nome)

    @model_validator(mode="after")
    def validar_referencia_ativa(self: Self) -> Self:
        """Rejeita referências ausentes ou diferentes das opções ativas."""
        type(self).validar_opcao_cache(self.id, self.nome)
        return self


class ProdutoLead(BaseModel):
    """Produto de interesse e seu mapeamento para o EXPA."""

    model_config = ConfigDict(extra="ignore")

    titulo: str
    id: PositiveInt
    id_expa: PositiveInt

    @model_validator(mode="after")
    def validar_produto(self: Self) -> Self:
        """Confere produto, título e programa EXPA como uma única combinação."""
        produtos_expa: dict[int, tuple[tuple[int, str], ...]] = {
            7: ((1, "Voluntário Global"),),
            8: (
                (2, "Talento Global Short Term"),
                (3, "Talento Global Mid e Long Term"),
            ),
            9: ((4, "Professor Global"),),
        }
        combinacoes_validas = produtos_expa.get(self.id_expa)
        if combinacoes_validas is None:
            raise ValueError("ID EXPA inválido; valores aceitos: 7, 8 ou 9.")
        if (self.id, self.titulo) not in combinacoes_validas:
            raise ValueError(
                "A combinação de ID e título não corresponde ao ID EXPA informado."
            )
        validar_opcao_cache("produto", self.id, self.titulo)
        return self


Produto = ProdutoLead


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
    """Área de atuação informada durante a qualificação."""

    external_id: ClassVar[str] = "area_atuacao"


class Idioma(ReferenciaLead):
    """Idioma informado durante a qualificação."""

    external_id: ClassVar[str] = "idiomas"


class NivelAtuacao(ReferenciaLead):
    """Nível de atuação informado durante a qualificação."""

    external_id: ClassVar[str] = "nivel_mercado"


class SemestreCurso(ReferenciaLead):
    """Semestre atual do curso informado durante a qualificação."""

    external_id: ClassVar[str] = "semestre_curso"


def _validar_data_nascimento(valor: datetime) -> datetime:
    """Rejeita datas de nascimento futuras."""
    if valor.date() > date.today():
        raise ValueError("A data de nascimento não pode ser uma data futura.")
    return valor


def _validar_tag(valor: str) -> str:
    """Exige tags minúsculas, sem espaços ou diacríticos."""
    if valor != valor.lower() or any(char.isspace() for char in valor):
        raise ValueError("A tag deve estar em minúsculas e não conter espaços.")
    if any(
        unicodedata.category(char) == "Mn"
        for char in unicodedata.normalize("NFD", valor)
    ):
        raise ValueError("A tag não pode conter acentos.")
    return valor


def _validar_senha(valor: str) -> str:
    """Aplica os critérios de senha usados no cadastro EXPA."""
    regras: tuple[tuple[bool, str], ...] = (
        (len(valor) >= 8, "A senha deve conter no mínimo 8 caracteres."),
        (not any(char.isspace() for char in valor), "A senha não pode conter espaços."),
        (
            not any(ord(char) < 32 for char in valor),
            "A senha contém caracteres de controle.",
        ),
        (
            not any(char in {";", "'", '"', "`", "\\"} for char in valor),
            "A senha contém caracteres não permitidos.",
        ),
        (bool(re.search(r"[a-z]", valor)), "A senha deve conter uma letra minúscula."),
        (bool(re.search(r"[A-Z]", valor)), "A senha deve conter uma letra maiúscula."),
        (bool(re.search(r"\d", valor)), "A senha deve conter um número."),
        (
            bool(re.search(r"[@$!%*?&]", valor)),
            "A senha deve conter um caractere especial (@$!%*?&).",
        ),
    )
    falhas = [mensagem for valida, mensagem in regras if not valida]
    if falhas:
        raise ValueError(" ".join(falhas))
    return valor


def _validar_nome_no_cache(valor: str) -> str:
    """Confere o nome de universidade no cache de divisão de mercado."""
    from app.cache import cache

    entrada = cache.store.get("metadados_universidades")
    dados = entrada.get("data") if isinstance(entrada, dict) else None
    universidades = dados.get("dados") if isinstance(dados, dict) else None
    if not isinstance(universidades, list):
        raise ValueError("Metadados de universidades indisponíveis no cache.")

    nome_normalizado = valor.strip().casefold()
    if any(
        isinstance(universidade, dict)
        and isinstance(universidade.get("nome"), str)
        and universidade["nome"].strip().casefold() == nome_normalizado
        for universidade in universidades
    ):
        return valor
    raise ValueError("O nome informado não corresponde a uma universidade válida.")


Universidade: TypeAlias = Annotated[str, AfterValidator(_validar_nome_no_cache)]
DataNascimento: TypeAlias = Annotated[
    datetime, AfterValidator(_validar_data_nascimento)
]
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


class CategoriaContato(str, Enum):
    """Categorias de e-mail e telefone reconhecidas pelo B2C."""

    HOME = "home"
    WORK = "work"
    MOBILE = "mobile"
    MAIN = "main"
    OTHER = "other"
    PRIVATE_FAX = "private_fax"
    WORK_FAX = "work_fax"

    @property
    def id_persistencia(self: Self) -> int:
        """Retorna o ID de persistência para a categoria ativa."""
        return buscar_id_opcao_cache("categoriaContato", self.value)


CATEGORIAS_EMAIL_VALIDAS: tuple[CategoriaContato, ...] = (
    CategoriaContato.HOME,
    CategoriaContato.WORK,
    CategoriaContato.OTHER,
)
CATEGORIAS_TELEFONE_VALIDAS: tuple[CategoriaContato, ...] = tuple(CategoriaContato)
CATEGORIAS_CONTATO_VALIDAS: dict[str, tuple[CategoriaContato, ...]] = {
    "email": CATEGORIAS_EMAIL_VALIDAS,
    "telefone": CATEGORIAS_TELEFONE_VALIDAS,
}


def listar_categorias_contato_validas() -> dict[str, list[str]]:
    """Retorna as categorias aceitas para cada tipo de contato."""
    return {
        campo: [categoria.value for categoria in categorias]
        for campo, categorias in CATEGORIAS_CONTATO_VALIDAS.items()
    }


class ContatoTelefone(BaseModel):
    """Telefone brasileiro informado pelo lead."""

    model_config = ConfigDict(extra="allow")
    tipo: CategoriaContato
    numero: str

    @field_validator("numero", mode="before")
    @classmethod
    def validar_numero(cls: type[Self], numero: object) -> str:
        """Exige celular brasileiro com DDD e onze dígitos."""
        valor = str(numero).strip() if numero else ""
        if not re.fullmatch(r"[1-9]{2}9[0-9]{8}", valor):
            raise ValueError(
                "O telefone deve conter DDD e celular brasileiro com 11 dígitos."
            )
        return valor

    @field_validator("tipo")
    @classmethod
    def validar_categoria_telefone(
        cls: type[Self], tipo: CategoriaContato
    ) -> CategoriaContato:
        """Confere a categoria de telefone nos metadados."""
        validar_texto_opcao_cache("categoriaContato", tipo.value)
        return tipo


class ContatoEmail(BaseModel):
    """Endereço de e-mail informado pelo lead."""

    model_config = ConfigDict(extra="allow")
    tipo: CategoriaContato
    email: EmailStr

    @field_validator("tipo")
    @classmethod
    def validar_categoria_email(
        cls: type[Self], tipo: CategoriaContato
    ) -> CategoriaContato:
        """Permite categorias compatíveis e ativas para e-mail."""
        if tipo not in CATEGORIAS_EMAIL_VALIDAS:
            raise ValueError(f"A categoria '{tipo.value}' não é permitida para e-mail.")
        validar_texto_opcao_cache("categoriaContato", tipo.value)
        return tipo


TelefoneItem = ContatoTelefone
EmailItem = ContatoEmail


class LeadPreCadastroBase(BaseModel):
    """Campos comuns aos formulários de pré-cadastro."""

    model_config = ConfigDict(extra="ignore")

    nome: str = Field(min_length=3, max_length=100, pattern=r"^[A-Za-zÀ-ÿ\s]+$")
    sobrenome: str = Field(min_length=3, max_length=100, pattern=r"^[A-Za-zÀ-ÿ\s]+$")
    dataNascimento: DataNascimento = Field(description="Data de nascimento")
    telefone: list[ContatoTelefone] = Field(min_length=1, max_length=2)
    email: list[ContatoEmail] = Field(min_length=1, max_length=2)
    universidade: Universidade | None = None
    produto: ProdutoLead
    comite: Comite | None = None
    autorizacao: Autorizacao
    origem: Origem
    meio: Meio | None = None
    tag: list[Tag] | None = None

    @field_validator("autorizacao")
    @classmethod
    def validar_autorizacao_metadados(
        cls: type[Self], valor: Autorizacao
    ) -> Autorizacao:
        """Confere o consentimento com as opções de privacidade B2C."""
        texto = "sim" if valor is Autorizacao.SIM else "não"
        validar_opcao_cache("termo_privacidade", int(valor), texto)
        return valor

    @model_validator(mode="after")
    def validar_universidade_ou_comite(self: Self) -> Self:
        """Exige universidade ou comitê para determinar a divisão de mercado."""
        if self.universidade is None and self.comite is None:
            raise ValueError("Informe ao menos um dos campos: universidade ou comite.")
        return self


MAX_PDF_SIZE_BYTES: int = 5 * 1024 * 1024


class UploadItem(BaseModel):
    """Arquivo PDF de currículo transportado em Base64."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    nome: str = Field(alias="fileName", description="Nome do arquivo PDF")
    base64: Base64Bytes = Field(
        max_length=MAX_PDF_SIZE_BYTES,
        description="Conteúdo do PDF codificado em Base64 (máximo de 5 MiB)",
    )

    @field_validator("nome")
    @classmethod
    def validar_extensao_pdf(cls: type[Self], nome: str) -> str:
        """Exige extensão PDF no nome do arquivo."""
        if not nome.lower().endswith(".pdf"):
            raise ValueError("O nome do arquivo deve ter a extensão '.pdf'.")
        return nome

    @field_validator("base64")
    @classmethod
    def validar_assinatura_pdf(cls: type[Self], conteudo: bytes) -> bytes:
        """Confere a assinatura PDF depois da decodificação Base64."""
        if not conteudo.startswith(b"%PDF"):
            raise ValueError("O conteúdo enviado não é um arquivo PDF válido.")
        return conteudo


__all__ = [
    "CATEGORIAS_CONTATO_VALIDAS",
    "CATEGORIAS_EMAIL_VALIDAS",
    "CATEGORIAS_TELEFONE_VALIDAS",
    "MAX_PDF_SIZE_BYTES",
    "AreaAtuacao",
    "Autorizacao",
    "CategoriaContato",
    "Comite",
    "ContatoEmail",
    "ContatoTelefone",
    "DataNascimento",
    "EmailItem",
    "Idioma",
    "LeadPreCadastroBase",
    "Meio",
    "NivelAtuacao",
    "Origem",
    "Produto",
    "ProdutoLead",
    "ReferenciaLead",
    "SemestreCurso",
    "Senha",
    "Tag",
    "TelefoneItem",
    "Universidade",
    "UploadItem",
    "buscar_id_opcao_cache",
    "listar_categorias_contato_validas",
    "validar_opcao_cache",
    "validar_texto_opcao_cache",
]
