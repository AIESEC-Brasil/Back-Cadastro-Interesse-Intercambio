"""Envelope genérico para respostas tipadas da API."""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class RetornoGenerico(BaseModel, Generic[T]):
    """Resposta genérica com indicador de sucesso e dados opcionais."""

    model_config = ConfigDict(extra="ignore")

    sucesso: bool = Field(default=True, description="Indica se a operação teve sucesso")
    data: T | None = Field(default=None, description="Dados da resposta")


__all__ = ["RetornoGenerico"]
