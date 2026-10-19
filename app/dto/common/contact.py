"""Modelos e categorias compartilhados pelos dados de contato."""

from enum import Enum
import re

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from .lead import buscar_id_opcao_cache, validar_texto_opcao_cache


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
    def id_persistencia(self) -> int:
        """Retorna o ID da categoria ativa, mantendo o texto recebido no DTO."""
        return buscar_id_opcao_cache("categoriaContato", self.value)


class ContatoTelefone(BaseModel):
    """Telefone informado pelo lead."""

    model_config = ConfigDict(extra="allow")

    tipo: CategoriaContato
    numero: str

    @field_validator("numero", mode="before")
    @classmethod
    def validar_numero(cls, numero: object) -> str:
        """Remove espaços externos e exige celular brasileiro com DDD."""
        valor: str = str(numero).strip() if numero else ""
        if not re.fullmatch(r"[1-9]{2}9[0-9]{8}", valor):
            raise ValueError("O telefone deve conter DDD e celular brasileiro com 11 dígitos.")
        return valor

    @field_validator("tipo")
    @classmethod
    def validar_categoria_telefone(cls, tipo: CategoriaContato) -> CategoriaContato:
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
    def validar_categoria_email(cls, tipo: CategoriaContato) -> CategoriaContato:
        """Permite somente categorias compatíveis com um endereço de e-mail."""
        permitidos = {
            CategoriaContato.HOME,
            CategoriaContato.WORK,
            CategoriaContato.OTHER,
        }
        if tipo not in permitidos:
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
