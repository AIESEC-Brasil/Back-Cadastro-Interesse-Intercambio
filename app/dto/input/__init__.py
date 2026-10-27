"""Modelos Pydantic para payloads recebidos pela API."""

from .lead import (
    AtualizarPreCadastroLead,
    CriarPreCadastroLead,
    LeadPreCadastroInput,
    QualificacaoLead,
)
from ..types import UploadItem

# ==============================================================================
# CONTRATOS RECEBIDOS PELA API
# ==============================================================================
__all__ = [
    "LeadPreCadastroInput",
    "CriarPreCadastroLead",
    "AtualizarPreCadastroLead",
    "QualificacaoLead",
    "UploadItem",
]
