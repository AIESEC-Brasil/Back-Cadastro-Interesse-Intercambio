"""DTOs de entrada para pré-cadastro e criação de leads."""

from pydantic import ConfigDict, Field
from typing import TypeAlias

from ..base import LeadPreCadastroBase

LeadPreCadastroInput: TypeAlias = LeadPreCadastroBase


class CriarPreCadastroLead(LeadPreCadastroInput):
    """Payload de criação de lead, incluindo a senha de acesso."""

    model_config = ConfigDict(extra="forbid")

    senha: str = Field(
        min_length=8,
        max_length=128,
        description="Senha de acesso do lead no EXPA",
    )


__all__ = ["LeadPreCadastroInput", "CriarPreCadastroLead"]
