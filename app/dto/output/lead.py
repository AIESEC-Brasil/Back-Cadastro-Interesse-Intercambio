"""DTO de saída para o cadastro de leads."""

from pydantic import ConfigDict, Field, PositiveInt

from ..types import LeadPreCadastroBase


# ==============================================================================
# RESPOSTA DO PRÉ-CADASTRO
# ==============================================================================
class LeadPreCadastroOutput(LeadPreCadastroBase):
    """Cadastro de lead retornado pela API, identificado pelo `id` atual."""

    model_config = ConfigDict(extra="forbid")

    id: PositiveInt = Field(description="Identificador do lead")


__all__ = ["LeadPreCadastroOutput"]
