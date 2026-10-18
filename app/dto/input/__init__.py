"""Modelos Pydantic para payloads recebidos pela API."""

from .leadCadastroDTO import CriarPreCadastroLead, LeadPreCadastroInput

__all__ = ["LeadPreCadastroInput", "CriarPreCadastroLead"]
