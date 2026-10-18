"""Contratos de dados da aplicação, organizados por tipo de uso."""

from . import base, globals, input, output, exception
from .base import LeadPreCadastroBase
from .exception import AppError, BaseErrorResponse, ErrorDetail, ValidationErrorResponse
from .globals import *
from .input import CriarPreCadastroLead, LeadPreCadastroInput
from .output import HttpStatus, Metadados

__all__ = [
    "base",
    "globals",
    "input",
    "output",
    "exception",
    "LeadPreCadastroBase",
    "Metadados",
    "HttpStatus",
    "LeadPreCadastroInput",
    "CriarPreCadastroLead",
    "AppError",
    "BaseErrorResponse",
    "ErrorDetail",
    "ValidationErrorResponse",
    *globals.__all__,
]
