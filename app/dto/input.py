"""Modelos de entrada usados pelas rotas e serviços."""

from typing import Literal, Self, TypeAlias

from pydantic import (
    BaseModel,
    Base64Bytes,
    ConfigDict,
    Field,
    PositiveInt,
    field_validator,
    model_validator,
)

from .types import (
    AreaAtuacao,
    ContatoEmail,
    ContatoTelefone,
    DataNascimento,
    Idioma,
    LeadPreCadastroBase,
    NivelAtuacao,
    Senha,
    SemestreCurso,
    UploadItem,
)


def _validar_id_metadado(external_id: str, valor: int) -> int:
    """Confere se um identificador pertence a uma opção ativa do B2C."""
    from ..utils.metadados import buscar_opcoes_metadado

    opcoes = buscar_opcoes_metadado(external_id)
    if not any(str(opcao.get("id")) == str(valor) for opcao in opcoes):
        raise ValueError(f"O ID {valor} não é uma opção ativa de '{external_id}'.")
    return valor

LeadPreCadastroInput: TypeAlias = LeadPreCadastroBase


class CriarPreCadastroB2C(LeadPreCadastroBase):
    """Entrada do formulário B2C sem senha ou criação de cadastro no EXPA."""

    model_config = ConfigDict(extra="forbid")


class CriarPreCadastroLead(LeadPreCadastroInput):
    """Entrada para criação de lead EXPA, incluindo a senha de acesso."""

    model_config = ConfigDict(extra="forbid")

    senha: Senha


class ValidarLinkConclusaoB2C(BaseModel):
    """Entrada para verificar se o pré-cadastro ainda pode ser concluído."""

    model_config = ConfigDict(extra="forbid")

    id: PositiveInt


class CompletarCadastroB2C(BaseModel):
    """Entrada do formulário de conclusão de cadastro B2C."""

    model_config = ConfigDict(extra="forbid")

    id: PositiveInt
    nome: str = Field(min_length=3, max_length=100, pattern=r"^[A-Za-zÀ-ÿ\s]+$")
    sobrenome: str = Field(min_length=3, max_length=100, pattern=r"^[A-Za-zÀ-ÿ\s]+$")
    emails: list[ContatoEmail] = Field(min_length=1, max_length=2)
    telefones: list[ContatoTelefone] = Field(min_length=1, max_length=2)
    dataNascimento: DataNascimento
    idProduto: PositiveInt
    idProgramaExpa: Literal[7, 8, 9]
    idComite: PositiveInt
    nomeCL: str = Field(min_length=1, max_length=150)
    idAutorizacao: Literal["1"]
    senha: Senha
    idiomas: list[PositiveInt] | None = None
    area_atuacao: PositiveInt | None = None
    nivel_mercado: PositiveInt | None = None
    curso: str | None = Field(default=None, max_length=100, pattern=r"^[A-Za-zÀ-ÿ\s]+$")
    semestre: PositiveInt | None = None
    file: Base64Bytes | None = Field(default=None, max_length=5 * 1024 * 1024)
    fileName: str | None = None

    @field_validator("idProduto")
    @classmethod
    def validar_produto(cls, valor: int) -> int:
        return _validar_id_metadado("produto", valor)

    @field_validator("idComite")
    @classmethod
    def validar_comite(cls, valor: int) -> int:
        return _validar_id_metadado("aiesec_proxima", valor)

    @field_validator("idiomas")
    @classmethod
    def validar_idiomas(cls, valores: list[int] | None) -> list[int] | None:
        if valores is not None:
            for valor in valores:
                _validar_id_metadado("idiomas", valor)
        return valores

    @field_validator("area_atuacao")
    @classmethod
    def validar_area_atuacao(cls, valor: int | None) -> int | None:
        if valor is not None:
            _validar_id_metadado("area_atuacao", valor)
        return valor

    @field_validator("nivel_mercado")
    @classmethod
    def validar_nivel_mercado(cls, valor: int | None) -> int | None:
        if valor is not None:
            _validar_id_metadado("nivel_mercado", valor)
        return valor

    @field_validator("semestre")
    @classmethod
    def validar_semestre(cls, valor: int | None) -> int | None:
        if valor is not None:
            _validar_id_metadado("semestre_curso", valor)
        return valor

    @field_validator("file")
    @classmethod
    def validar_curriculo_pdf(cls, conteudo: bytes | None) -> bytes | None:
        """Aceita somente conteúdo PDF válido no currículo opcional."""
        if conteudo is not None and not conteudo.startswith(b"%PDF"):
            raise ValueError("O conteúdo enviado não é um arquivo PDF válido.")
        return conteudo

    @field_validator("fileName")
    @classmethod
    def validar_nome_curriculo(cls, nome: str | None) -> str | None:
        """Exige a extensão PDF no nome do arquivo enviado."""
        if nome is not None and not nome.lower().endswith(".pdf"):
            raise ValueError("O nome do arquivo deve ter a extensão '.pdf'.")
        return nome

    @model_validator(mode="after")
    def validar_curriculo_completo(self) -> Self:
        """Exige conteúdo e nome juntos quando há envio de currículo."""
        if (self.file is None) != (self.fileName is None):
            raise ValueError("Envie o arquivo e o nome do currículo juntos.")
        produtos_validos = {7: {1}, 8: {2, 3}, 9: {4}}
        if self.idProduto not in produtos_validos[self.idProgramaExpa]:
            raise ValueError("O produto não corresponde ao programa informado.")
        return self


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
    "CompletarCadastroB2C",
    "CriarPreCadastroB2C",
    "CriarPreCadastroLead",
    "LeadPreCadastroInput",
    "QualificacaoLead",
]
