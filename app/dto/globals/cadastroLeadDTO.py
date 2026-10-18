"""Tipos reutilizáveis nos payloads de cadastro de leads."""

from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel, ConfigDict, PositiveInt


class ContatoTelefone(BaseModel):
    """Telefone informado pelo lead."""

    model_config = ConfigDict(extra="allow")

    tipo: str
    numero: str


class ContatoEmail(BaseModel):
    """E-mail informado pelo lead."""

    model_config = ConfigDict(extra="allow")

    tipo: str
    email: str


class ReferenciaLead(BaseModel):
    """Referência a uma universidade, comitê, origem ou meio."""

    model_config = ConfigDict(extra="allow")

    id: PositiveInt
    nome: str


class ProdutoLead(BaseModel):
    """Produto escolhido no formulário de interesse."""

    model_config = ConfigDict(extra="ignore")

    titulo: str
    id: PositiveInt


DataNascimento = datetime


class Autorizacao(IntEnum):
    """Valores numéricos de consentimento aceitos no payload."""

    NAO = 0
    SIM = 1


Tag = str

__all__ = [
    "Autorizacao",
    "ContatoEmail",
    "ContatoTelefone",
    "DataNascimento",
    "ProdutoLead",
    "ReferenciaLead",
    "Tag",
]
