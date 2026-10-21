"""DTO do payload de criação de lead enviado à integração EXPA."""

from pydantic import BaseModel, ConfigDict, Field, PositiveInt


# ==============================================================================
# PAYLOAD ENVIADO AO WEBHOOK EXPA
# ==============================================================================
class PayloadExpa(BaseModel):
    """Representa o payload plano recebido pelo Apps Script de integração EXPA."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    nome: str
    sobrenome: str
    senha: str
    data_nascimento: str = Field(serialization_alias="dataNascimento")
    programa: PositiveInt
    nome_cl: str = Field(serialization_alias="nomeCL")
    telefone: str
    email: str
    token_expa: str = Field(
        min_length=1,
        repr=False,
        serialization_alias="tokenExpa",
    )


__all__ = ["PayloadExpa"]
