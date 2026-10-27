"""Modelos e exceções para respostas de erro da API."""

import logging
from ast import literal_eval
from typing import Any, Self

from deep_translator import GoogleTranslator
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ..output import HttpStatus

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


# ==============================================================================
# CONTRATOS DE ERRO HTTP
# ==============================================================================
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
        self: Self,
        type: str,
        message: str,
        status_code: HttpStatus = HttpStatus.UNPROCESSABLE_ENTITY,
        error_details: list[dict[str, Any]] | None = None,
    ) -> None:
        """Monta a resposta estruturada e inicializa a exceção base.

        Args:
            type: Categoria identificável do erro.
            message: Mensagem apresentada ao cliente.
            status_code: Status HTTP associado ao erro.
            error_details: Detalhes opcionais sobre campos ou causas específicas.
        """
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


# ==============================================================================
# CONVERSÃO DOS ERROS DE VALIDAÇÃO
# ==============================================================================
class ValidationErrorResponse(BaseErrorResponse):
    """Resposta 422 com mensagens traduzidas e campos inválidos identificados."""

    status_code: HttpStatus = HttpStatus.UNPROCESSABLE_ENTITY

    @classmethod
    def from_exception(
        cls: type[Self], exception: ValidationError
    ) -> Self:
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

            message: str | None = VALIDATION_MESSAGES_PT.get(error["type"])
            if message is None:
                try:
                    message = GoogleTranslator(
                        source="auto", target="pt"
                    ).translate(original_message)
                except Exception:
                    logger.warning(
                        "Falha ao traduzir erro de validação do tipo %s",
                        error["type"],
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


__all__ = ["AppError", "BaseErrorResponse", "ErrorDetail", "ValidationErrorResponse"]
