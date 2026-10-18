"""Modelos de erro publicados pela API."""

from .exceptionsDTO import AppError, BaseErrorResponse, ErrorDetail, ValidationErrorResponse

__all__ = ["AppError", "BaseErrorResponse", "ErrorDetail", "ValidationErrorResponse"]
