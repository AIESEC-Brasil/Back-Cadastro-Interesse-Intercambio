"""Mapeia exceções para os DTOs padronizados de erro."""

from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from ..dto import HttpStatus
from ..dto import AppError, BaseErrorResponse, ValidationErrorResponse


def resolve_exception(exception: Exception) -> BaseErrorResponse:
    """Converte validações, erros HTTP e exceções comuns para o DTO de erro."""
    if isinstance(exception, AppError):
        return exception.dto
    if isinstance(exception, ValidationError):
        return ValidationErrorResponse.from_exception(exception)
    if isinstance(exception, HTTPException):
        code: int = exception.code or HttpStatus.INTERNAL_SERVER_ERROR.value
        try:
            status_code: HttpStatus = HttpStatus(code)
        except ValueError:
            status_code = HttpStatus.INTERNAL_SERVER_ERROR
        return BaseErrorResponse(
            type=exception.__class__.__name__,
            message=exception.description or "Ocorreu um erro HTTP.",
            status_code=status_code,
        )
    return BaseErrorResponse(
        type=exception.__class__.__name__,
        message=str(exception) or "Ocorreu um erro interno.",
        status_code=HttpStatus.INTERNAL_SERVER_ERROR,
    )


__all__ = ["resolve_exception"]
