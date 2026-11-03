"""Exceções e modelos padronizados de erro da API."""

import logging
from ast import literal_eval
from typing import Any, Self

from deep_translator import GoogleTranslator
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .output import HttpStatus

logger: logging.Logger = logging.getLogger(__name__)

VALIDATION_MESSAGES_PT: dict[str, str] = {
    "bool_parsing": "Informe um valor verdadeiro ou falso.",
    "bool_type": "O valor deve ser verdadeiro ou falso.",
    "float_parsing": "Informe um número válido.",
    "float_type": "O valor deve ser um número.",
    "int_parsing": "Informe um número inteiro válido.",
    "int_type": "O valor deve ser um número inteiro.",
    "list_type": "O valor deve ser uma lista.",
    "missing": "Este campo é obrigatório.",
    "model_type": "O valor informado possui um formato inválido.",
    "string_too_long": "O texto informado é muito longo.",
    "string_too_short": "O texto informado é muito curto.",
    "string_type": "O valor deve ser um texto.",
}


class ErrorDetail(BaseModel):
    """Campo e motivo associados a um erro de validação."""

    loc: str = Field(description="Caminho do campo inválido")
    msg: str = Field(description="Motivo da falha de validação")


class BaseErrorResponse(BaseModel):
    """Contrato JSON comum para erros HTTP."""

    model_config = ConfigDict(use_enum_values=True)
    error: bool = True
    type: str
    message: str
    error_details: list[ErrorDetail] = Field(default_factory=list)
    status_code: HttpStatus = HttpStatus.INTERNAL_SERVER_ERROR


class AppError(Exception):
    """Erro de negócio com status HTTP e detalhes controlados."""

    def __init__(
        self: Self,
        type: str,
        message: str,
        status_code: HttpStatus = HttpStatus.UNPROCESSABLE_ENTITY,
        error_details: list[dict[str, Any]] | None = None,
    ) -> None:
        """Cria a resposta tipada associada ao erro de negócio."""
        self.dto = BaseErrorResponse(
            type=type,
            message=message,
            status_code=status_code,
            error_details=[
                ErrorDetail.model_validate(detail) for detail in (error_details or [])
            ],
        )
        super().__init__(message)


class ValidationErrorResponse(BaseErrorResponse):
    """Resposta 422 com erros Pydantic traduzidos para português."""

    status_code: HttpStatus = HttpStatus.UNPROCESSABLE_ENTITY

    @classmethod
    def from_exception(cls: type[Self], exception: ValidationError) -> Self:
        """Converte erros Pydantic mantendo a localização de cada campo."""
        details: list[ErrorDetail] = []
        seen: set[tuple[str, str]] = set()

        for error in exception.errors():
            location = " -> ".join(str(part) for part in error["loc"])
            original_message = error["msg"]
            key = (location, original_message)
            if key in seen:
                continue
            seen.add(key)

            message = VALIDATION_MESSAGES_PT.get(error["type"])
            if message is None:
                try:
                    message = GoogleTranslator(source="auto", target="pt").translate(
                        original_message
                    )
                except Exception:
                    logger.exception(
                        "Falha bruta na tradução da validação | tipo=%s | mensagem=%r",
                        error["type"],
                        original_message,
                    )
                    message = "Valor inválido."

            message = message.removeprefix("Value error, ")
            if message.startswith("["):
                try:
                    message = str(literal_eval(message))
                except (SyntaxError, ValueError):
                    pass
            details.append(ErrorDetail(loc=location, msg=message))

        return cls(
            type="ValidationError",
            message="Dados inválidos",
            error_details=details,
            status_code=HttpStatus.UNPROCESSABLE_ENTITY,
        )


__all__ = [
    "VALIDATION_MESSAGES_PT",
    "AppError",
    "BaseErrorResponse",
    "ErrorDetail",
    "ValidationErrorResponse",
]
