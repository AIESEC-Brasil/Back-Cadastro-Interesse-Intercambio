"""Tipos compartilhados entre os DTOs de entrada e saída."""

from .contact import (
    CategoriaContato,
    ContatoEmail,
    ContatoTelefone,
    EmailItem,
    TelefoneItem,
)
from .expa import PayloadExpa
from .lead import (
    AreaAtuacao,
    Autorizacao,
    Comite,
    DataNascimento,
    Idioma,
    Meio,
    NivelAtuacao,
    Origem,
    Produto,
    ProdutoLead,
    ReferenciaLead,
    Senha,
    SemestreCurso,
    Tag,
    Universidade,
)

__all__ = [
    "AreaAtuacao",
    "Autorizacao",
    "CategoriaContato",
    "Comite",
    "ContatoEmail",
    "ContatoTelefone",
    "DataNascimento",
    "EmailItem",
    "Idioma",
    "Meio",
    "NivelAtuacao",
    "Origem",
    "PayloadExpa",
    "ProdutoLead",
    "Produto",
    "ReferenciaLead",
    "Senha",
    "SemestreCurso",
    "Tag",
    "TelefoneItem",
    "Universidade",
]
