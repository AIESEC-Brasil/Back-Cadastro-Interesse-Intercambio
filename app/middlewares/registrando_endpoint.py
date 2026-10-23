"""Auditoria de requisições e políticas de cache das respostas."""

import logging
from time import perf_counter
from typing import Callable

from flask import Response, render_template, request

from ..dto.output import HttpStatus

# ==============================================================================
# CONFIGURAÇÃO DE AUDITORIA E CACHE HTTP
# ==============================================================================
logger: logging.Logger = logging.getLogger(__name__)
error_logger: logging.Logger = logging.getLogger("app.http.errors")

NO_CACHE_ROUTES: set[str] = {
    "/api/docs",
    "/openapi",
    "/openapi/scalar",
    "/openapi/redoc",
    "/openapi/elements",
    "/openapi/rapidoc",
    "/openapi/rapipdf",
    "/openapi/openapi.json",
    "/apidoc/openapi.json",
}

NO_CACHE_PREFIXES: tuple[str, ...] = (
    "/static/",
    "/openapi/swagger",
    "/apidoc/swagger",
    "/openapi/static/",
    "/openapi/redoc/",
    "/openapi/scalar/",
)

IGNORED_ERROR_PATHS: set[str] = {"/favicon.ico"}

ERROR_MESSAGES: dict[int, str] = {
    HttpStatus.BAD_REQUEST: "A solicitação não pôde ser entendida pelo servidor.",
    HttpStatus.UNAUTHORIZED: "Você não tem autorização para acessar este recurso.",
    HttpStatus.FORBIDDEN: "O acesso a este recurso foi bloqueado.",
    HttpStatus.NOT_FOUND: "A página solicitada não foi encontrada.",
    HttpStatus.METHOD_NOT_ALLOWED: "Este método não é permitido para este endereço.",
    HttpStatus.REQUEST_TIMEOUT: "O servidor demorou para responder à solicitação.",
    HttpStatus.CONFLICT: "A solicitação entrou em conflito com o estado atual do recurso.",
    HttpStatus.UNPROCESSABLE_ENTITY: "Os dados enviados não puderam ser processados.",
    HttpStatus.TOO_MANY_REQUESTS: "Foram feitas muitas solicitações. Tente novamente em instantes.",
    HttpStatus.INTERNAL_SERVER_ERROR: "Ocorreu um erro interno. Tente novamente mais tarde.",
    HttpStatus.BAD_GATEWAY: "Um serviço necessário respondeu de forma inesperada.",
    HttpStatus.SERVICE_UNAVAILABLE: "O serviço está temporariamente indisponível.",
    HttpStatus.GATEWAY_TIMEOUT: "Um serviço necessário demorou para responder.",
}


REQUEST_STARTED_AT: str = "app.request_started_at"


# ==============================================================================
# CALLBACKS DE REQUISIÇÃO E RESPOSTA
# ==============================================================================
def capture_request_start() -> None:
    """Marca o início da requisição para calcular sua duração no log."""
    request.environ[REQUEST_STARTED_AT] = perf_counter()


def register_url(response: Response) -> Response:
    """Registra os dados de acesso e define a política de cache da resposta."""
    started_at: float = request.environ.get(REQUEST_STARTED_AT, perf_counter())
    duration_ms: float = (perf_counter() - started_at) * 1000
    forwarded_for: str = request.headers.get("X-Forwarded-For", "")
    client_ip: str = (
        forwarded_for.split(",", 1)[0].strip() or request.remote_addr or "-"
    )
    peer_ip: str = request.remote_addr or "-"

    if request.path not in IGNORED_ERROR_PATHS:
        logger.info(
            "Requisição HTTP | IP cliente=%s | IP conexão=%s | método=%s | "
            "endpoint=%s | protocolo=%s | status=%s | duração=%.2f ms | agente=%r",
            client_ip,
            peer_ip,
            request.method,
            request.path,
            request.environ.get("SERVER_PROTOCOL", "HTTP/1.1"),
            response.status_code,
            duration_ms,
            request.user_agent.string,
        )

    if (
        response.status_code >= 400 and response.status_code != 401
        and response.status_code != HttpStatus.UNPROCESSABLE_ENTITY
        and request.path not in IGNORED_ERROR_PATHS
    ):
        try:
            status_name: str = HttpStatus(response.status_code).name
        except ValueError:
            status_name = "HTTP_ERROR"

        log_error: Callable[..., None] = (
            error_logger.error
            if response.status_code >= 500
            else error_logger.warning
        )
        log_error(
            "Requisição HTTP rejeitada | HTTP %s %s | método=%s | endpoint=%s | "
            "IP cliente=%s",
            response.status_code,
            status_name,
            request.method,
            request.path,
            client_ip,
        )

        message: str = ERROR_MESSAGES.get(
            response.status_code,
            "Ocorreu um erro ao processar sua solicitação.",
        )
        # Mantém o status HTTP original e troca somente o corpo por uma página legível.
        response.set_data(
            render_template(
                "error.html",
                status_code=response.status_code,
                status_name=status_name,
                message=message,
            )
        )
        response.mimetype = "text/html"

    if request.path in NO_CACHE_ROUTES or request.path.startswith(NO_CACHE_PREFIXES):
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    else:
        response.headers["Cache-Control"] = "public, max-age=7200, must-revalidate"

    return response


__all__ = ["capture_request_start", "register_url"]
