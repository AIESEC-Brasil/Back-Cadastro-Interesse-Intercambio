"""Modelos e enums usados nas respostas da API."""

from .http_status import HttpStatus
from .conflicts import ConflitoEmail, ConflitoTelefone, ConflitosLeadOutput
from .generic import RetornoGenerico
from .lead import LeadPreCadastroOutput
from .metadata import (
    CampoMetadado,
    ConfiguracaoMetadado,
    ConfiguracoesCampo,
    DadosMetadados,
    Metadados,
)

__all__ = [
    "CampoMetadado",
    "ConflitoEmail",
    "ConflitoTelefone",
    "ConflitosLeadOutput",
    "ConfiguracaoMetadado",
    "ConfiguracoesCampo",
    "DadosMetadados",
    "HttpStatus",
    "LeadPreCadastroOutput",
    "Metadados",
    "RetornoGenerico",
]
