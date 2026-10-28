"""DTOs da estrutura de metadados retornada pelo Apps Script B2C."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from typing import Self
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_serializer


# ==============================================================================
# SCHEMAS DOS METADADOS B2C
# ==============================================================================
class ConfiguracoesCampo(BaseModel):
    """
    Configurações de um campo de metadado.
    """
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
    categorias_contato: Dict[str, List[str]]


class Metadados(BaseModel):
    """Resposta de metadados com os dados B2C e o horário da atualização."""

    data: DadosMetadados
    timestamp: datetime | str = Field(
        serialization_alias="timestamp",
        description="Data e hora em que os metadados foram atualizados no cache"
    )

    @field_serializer("timestamp")
    def formatar_timestamp_pt_br(
        self: Self, valor: datetime | str
    ) -> str:
        """Serializa o timestamp no formato legível usado pelas versões antigas."""
        if isinstance(valor, str):
            return valor
        valor = valor.astimezone(ZoneInfo("America/Sao_Paulo"))
        dias: tuple[str, ...] = (
            "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
            "sexta-feira", "sábado", "domingo",
        )
        meses: tuple[str, ...] = (
            "janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
        )
        return (
            f"{dias[valor.weekday()].capitalize()}, {valor.day:02d} de "
            f"{meses[valor.month - 1].capitalize()} de {valor.year}, "
            f"{valor:%H:%M:%S}"
        )


__all__ = [
    "CampoMetadado",
    "ConfiguracaoMetadado",
    "ConfiguracoesCampo",
    "DadosMetadados",
    "Metadados",
]
