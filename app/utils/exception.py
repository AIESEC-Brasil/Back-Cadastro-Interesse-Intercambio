"""Callbacks de erro usados pelo Flask-OpenAPI3 e pela aplicação."""

from typing import Any

from flask import Response, jsonify, make_response
from flask_openapi3.utils import run_validate_response
from pydantic import BaseModel, ValidationError

from ..dto.exception import AppError
from .resolve import resolve_exception


def handle_validation_error(exception: ValidationError) -> Response:
    """Formata erros de validação do OpenAPI como resposta JSON HTTP 422."""
    error = resolve_exception(exception)
    status = int(error.status_code)
    return make_response(jsonify(error.model_dump(mode="json")), status)


def handle_app_error(exception: AppError) -> tuple[dict[str, Any], int]:
    """Serializa erros de negócio lançados como ``AppError``."""
    error = exception.dto
    return error.model_dump(mode="json"), int(error.status_code)


def validate_api_response(response: Any, responses: dict[Any, Any] | None = None) -> Any:
    """Valida respostas declaradas com DTOs e ignora metadados OpenAPI em dicionários."""
    response_models = {
        status: model
        for status, model in (responses or {}).items()
        if isinstance(model, type) and issubclass(model, BaseModel)
    }
    return run_validate_response(response, response_models)


__all__ = [
    "handle_validation_error",
    "handle_app_error",
    "validate_api_response",
]
