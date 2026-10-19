"""Modelos e exceções para respostas de erro da API."""

from .errors import AppError, BaseErrorResponse, ErrorDetail, ValidationErrorResponse

__all__ = ["AppError", "BaseErrorResponse", "ErrorDetail", "ValidationErrorResponse"]
