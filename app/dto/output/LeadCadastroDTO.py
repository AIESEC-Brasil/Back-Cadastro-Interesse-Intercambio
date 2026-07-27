from pydantic import (
    Field,           # Utilizado para definir metadados dos campos, descrições, aliases e exemplos para o JSON Schema.
)
from ..input import LeadPreCadastroInput # modelo de transferencia dos dados de entrada

class LeadPreCadastroOutput(LeadPreCadastroInput):
    """
    Retorna os dados de entrada mais o item_id do card do lead
    """
    item_id: int = Field(...,description="O id do card do Lead no podio", json_schema_extra={"exemple":"325664"})

__all__ = ["LeadPreCadastroOutput"]