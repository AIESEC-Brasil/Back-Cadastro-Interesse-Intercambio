"""Schema dos dados retornados pelos Apps Scripts de divisão de mercado."""

from datetime import datetime
from typing import Any, Self
from zoneinfo import ZoneInfo
from pydantic import BaseModel, ConfigDict, Field, field_serializer


# ==============================================================================
# RESPOSTA DA DIVISÃO DE MERCADO
# ==============================================================================
class DivisaoMercadoMetadados(BaseModel):
    """Resposta de escritórios ou universidades com seus dados originais."""

    model_config = ConfigDict(extra="allow")

    recurso: str
    path: str
    aba: str
    total: int
    dados: list[dict[str, Any]]
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


__all__ = ["DivisaoMercadoMetadados"]
