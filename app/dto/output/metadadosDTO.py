"""DTOs da estrutura de metadados retornada pelo Apps Script B2C."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ConfiguracoesCampo(BaseModel):
    """Configurações de um campo de metadado."""
    model_config = ConfigDict(extra="allow")

    description: Optional[str] = None
    options: List[Dict[str, Any]] = Field(default_factory=list)


class ConfiguracaoMetadado(BaseModel):
    """Configurações de um metadado."""
    model_config = ConfigDict(extra="allow")

    settings: ConfiguracoesCampo


class CampoMetadado(BaseModel):
    """Campo de metadado retornado pelo Apps Script B2C."""
    model_config = ConfigDict(extra="allow")

    external_id: str
    config: ConfiguracaoMetadado


class DadosMetadados(BaseModel):
    """Dados de metadados retornados pelo Apps Script B2C."""
    fields: List[CampoMetadado]


class Metadados(BaseModel):
    """Resposta do endpoint: ``{"data": {"fields": [...]}}``."""

    data: DadosMetadados


__all__ = ["Metadados"]
