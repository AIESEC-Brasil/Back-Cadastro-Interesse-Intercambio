"""Utilitário para acesso aos campos de metadados em cache."""

from .metadados import buscar_campo_metadado, buscar_opcoes_metadado
from .exception import handle_app_error, handle_validation_error, validate_api_response
from .payload import (
    montar_dto_persistencia,
    montar_payload_expa,
    montar_payload_persistencia,
    payload_expa,
)

# ==============================================================================
# UTILITÁRIOS PÚBLICOS
# ==============================================================================
__all__ = [
    "buscar_campo_metadado",
    "buscar_opcoes_metadado",
    "handle_app_error",
    "handle_validation_error",
    "validate_api_response",
    "montar_dto_persistencia",
    "montar_payload_persistencia",
    "montar_payload_expa",
    "payload_expa",
]
