"""Callbacks de erro usados pelo Flask-OpenAPI3 e pela aplicação."""

from typing import Any

from flask import Response, jsonify, make_response
from flask_openapi3.utils import run_validate_response
from pydantic import BaseModel, ValidationError

from ..dto import AppError, BaseErrorResponse
from .resolve import resolve_exception


def handle_validation_error(exception: ValidationError) -> Response:
    """Formata erros de validação do OpenAPI como resposta JSON HTTP 422."""
    error: BaseErrorResponse = resolve_exception(exception)
    status: int = int(error.status_code)
    return make_response(jsonify(error.model_dump(mode="json")), status)


def handle_app_error(exception: AppError) -> tuple[dict[str, Any], int]:
    """Serializa erros de negócio lançados como ``AppError``."""
    error: BaseErrorResponse = exception.dto
    return error.model_dump(mode="json"), int(error.status_code)


def validate_api_response(response: Any, responses: dict[Any, Any] | None = None) -> Any:
    """Valida e serializa respostas declaradas com DTOs Pydantic."""
    response_models: dict[str | int, type[BaseModel] | dict[Any, Any] | None] = {
        status: model
        for status, model in (responses or {}).items()
        if isinstance(model, type) and issubclass(model, BaseModel)
    }
    run_validate_response(response, response_models)

    payload: Any
    status: Any
    if isinstance(response, tuple):
        payload, status = response[:2]
    elif isinstance(response, Response):
        # Flask Response já está serializada; a validação anterior ainda verifica
        # respostas JSON declaradas sem alterar headers ou status.
        return response
    else:
        payload, status = response, 200

    status = getattr(status, "value", status)
    response_model: type[BaseModel] | None = response_models.get(status)
    if response_model is None:
        return response

    serialized: dict[str, Any] = response_model.model_validate(payload).model_dump(
        mode="json", by_alias=True
    )
    if isinstance(response, tuple):
        return (serialized, *response[1:])
    return serialized


__all__ = [
    "handle_validation_error",
    "handle_app_error",
    "validate_api_response",
]
