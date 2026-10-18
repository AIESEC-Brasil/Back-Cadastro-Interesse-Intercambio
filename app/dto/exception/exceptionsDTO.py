"""Modelos e exceções para respostas de erro da API."""

from ast import literal_eval
from typing import Any

from deep_translator import GoogleTranslator
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ..output import HttpStatus


class ErrorDetail(BaseModel):
    """Detalhe de um campo que falhou na validação."""

    loc: str = Field(description="Caminho do campo inválido")
    msg: str = Field(description="Motivo da falha de validação")


class BaseErrorResponse(BaseModel):
    """Formato JSON padronizado para erros retornados pela API."""

    model_config = ConfigDict(use_enum_values=True)

    error: bool = True
    type: str
    message: str
    error_details: list[ErrorDetail] = Field(default_factory=list)
    status_code: HttpStatus = HttpStatus.INTERNAL_SERVER_ERROR


class AppError(Exception):
    """Erro controlado da aplicação com status e detalhes personalizados."""

    def __init__(
        self,
        type: str,
        message: str,
        status_code: HttpStatus = HttpStatus.UNPROCESSABLE_ENTITY,
        error_details: list[dict[str, Any]] | None = None,
    ) -> None:
        self.dto = BaseErrorResponse(
            type=type,
            message=message,
            status_code=status_code,
            error_details=[
                ErrorDetail.model_validate(detail)
                for detail in (error_details or [])
            ],
        )
        super().__init__(message)


class ValidationErrorResponse(BaseErrorResponse):
    """Resposta 422 com mensagens traduzidas e campos inválidos identificados."""

    status_code: HttpStatus = HttpStatus.UNPROCESSABLE_ENTITY

    @classmethod
    def from_exception(cls, exception: ValidationError) -> "ValidationErrorResponse":
        """Converte os erros Pydantic para o formato de erro da aplicação."""
        details: list[ErrorDetail] = []
        seen: set[tuple[str, str]] = set()

        for error in exception.errors():
            location: str = " -> ".join(str(part) for part in error["loc"])
            original_message: str = error["msg"]
            key: tuple[str, str] = (location, original_message)
            if key in seen:
                continue
            seen.add(key)

            try:
                message: str = GoogleTranslator(source="auto", target="pt").translate(
                    original_message
                )
            except Exception:
                message = original_message

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


__all__ = ["AppError", "BaseErrorResponse", "ErrorDetail", "ValidationErrorResponse"]
