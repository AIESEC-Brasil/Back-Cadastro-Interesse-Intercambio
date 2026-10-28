"""Modelos e categorias compartilhados pelos dados de contato."""

from enum import Enum
import re
from typing import Self

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from .lead import buscar_id_opcao_cache, validar_texto_opcao_cache


# ==============================================================================
# CATEGORIAS E DADOS DE CONTATO
# ==============================================================================
class CategoriaContato(str, Enum):
    """Categorias aceitas no campo `tipo` dos contatos."""

    HOME = "home"
    WORK = "work"
    MOBILE = "mobile"
    MAIN = "main"
    OTHER = "other"
    PRIVATE_FAX = "private_fax"
    WORK_FAX = "work_fax"

    @property
    def id_persistencia(self: Self) -> int:
        """Retorna o ID da categoria ativa, mantendo o texto recebido no DTO."""
        return buscar_id_opcao_cache("categoriaContato", self.value)


CATEGORIAS_EMAIL_VALIDAS = (
    CategoriaContato.HOME,
    CategoriaContato.WORK,
    CategoriaContato.OTHER,
)
CATEGORIAS_TELEFONE_VALIDAS = tuple(CategoriaContato)
CATEGORIAS_CONTATO_VALIDAS = {
    "email": CATEGORIAS_EMAIL_VALIDAS,
    "telefone": CATEGORIAS_TELEFONE_VALIDAS,
}


def listar_categorias_contato_validas() -> dict[str, list[str]]:
    """Retorna as categorias aceitas por tipo de contato para os clientes."""
    return {
        campo: [categoria.value for categoria in categorias]
        for campo, categorias in CATEGORIAS_CONTATO_VALIDAS.items()
    }


class ContatoTelefone(BaseModel):
    """Telefone informado pelo lead."""

    model_config = ConfigDict(extra="allow")

    tipo: CategoriaContato
    numero: str

    @field_validator("numero", mode="before")
    @classmethod
    def validar_numero(cls: type[Self], numero: object) -> str:
        """Remove espaços externos e exige celular brasileiro com DDD."""
        valor: str = str(numero).strip() if numero else ""
        if not re.fullmatch(r"[1-9]{2}9[0-9]{8}", valor):
            raise ValueError("O telefone deve conter DDD e celular brasileiro com 11 dígitos.")
        return valor

    @field_validator("tipo")
    @classmethod
    def validar_categoria_telefone(
        cls: type[Self], tipo: CategoriaContato
    ) -> CategoriaContato:
        """Confere a categoria de telefone nas opções de `categoriaContato`."""
        validar_texto_opcao_cache("categoriaContato", tipo.value)
        return tipo


class ContatoEmail(BaseModel):
    """E-mail informado pelo lead."""

    model_config = ConfigDict(extra="allow")

    tipo: CategoriaContato
    email: EmailStr

    @field_validator("tipo")
    @classmethod
    def validar_categoria_email(
        cls: type[Self], tipo: CategoriaContato
    ) -> CategoriaContato:
        """Permite somente categorias compatíveis com um endereço de e-mail."""
        if tipo not in CATEGORIAS_EMAIL_VALIDAS:
            raise ValueError(f"A categoria '{tipo.value}' não é permitida para e-mail.")
        validar_texto_opcao_cache("categoriaContato", tipo.value)
        return tipo


TelefoneItem = ContatoTelefone
EmailItem = ContatoEmail


__all__ = [
    "CategoriaContato",
    "ContatoEmail",
    "ContatoTelefone",
    "EmailItem",
    "TelefoneItem",
]
