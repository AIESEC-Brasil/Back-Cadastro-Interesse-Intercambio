"""Modelos Pydantic para payloads recebidos pela API."""

from .lead import (
    AtualizarPreCadastroLead,
    CriarPreCadastroLead,
    LeadPreCadastroInput,
    QualificacaoLead,
)
from .upload import UploadItem

__all__ = [
    "LeadPreCadastroInput",
    "CriarPreCadastroLead",
    "AtualizarPreCadastroLead",
    "QualificacaoLead",
    "UploadItem",
]
