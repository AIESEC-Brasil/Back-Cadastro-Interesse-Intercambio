"""Schemas de resposta para conflitos de e-mail e telefone."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ==============================================================================
# CONFLITOS DE CONTATO
# ==============================================================================
class ConflitoEmail(BaseModel):
    """E-mail que já existe no cadastro."""

    email: EmailStr = Field(description="E-mail em conflito")


class ConflitoTelefone(BaseModel):
    """Telefone que já existe no cadastro."""

    numero: str = Field(description="Telefone em conflito")


class ConflitosLeadOutput(BaseModel):
    """Conflitos encontrados para um lead."""

    model_config = ConfigDict(extra="forbid")

    emails: list[ConflitoEmail] | None = None
    telefone: list[ConflitoTelefone] | None = None


__all__ = ["ConflitoEmail", "ConflitoTelefone", "ConflitosLeadOutput"]
