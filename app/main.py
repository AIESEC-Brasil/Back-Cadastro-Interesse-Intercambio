"""Fábrica da API de cadastro de interesse em intercâmbio."""

import os

from asgiref.sync import async_to_sync
from flask_cors import CORS
from flask_openapi3 import Info, OpenAPI

from .api import api
from .controller import cadastro_lead_view, divisao_mercado, new_lead_ogx
from .core import IS_DEV, pre_carregamento_metadados, setup_logging
from .dto.exception import AppError, ValidationErrorResponse
from .middlewares import (
    capture_request_start,
    injetar_css_no_elements,
    register_url,
    verificar_origem,
)
from .router import ApiOpenAPI
from .utils.exception import (
    handle_app_error,
    handle_validation_error,
    validate_api_response,
)


# ==============================================================================
# FÁBRICA E CONFIGURAÇÃO DA APLICAÇÃO
# ==============================================================================
def create_app() -> OpenAPI:
    """Cria e configura a aplicação, as rotas, os logs e o cache inicial.

    Returns:
        Instância Flask/OpenAPI pronta para ser servida pelo servidor WSGI.
    """
    setup_logging(debug=IS_DEV)
    app: OpenAPI = ApiOpenAPI(
        __name__,
        info=Info(title="Cadastro de Interesse em Intercâmbio", version="1.0.0"),
        validation_error_status=422,
        validation_error_model=ValidationErrorResponse,
        validation_error_callback=handle_validation_error,
        validate_response=True,
        validate_response_callback=validate_api_response,
    )
    app.config["ELEMENTS_CONFIG"] = {
        "layout": "sidebar",
        "hideTryIt": False,
        "router": "hash"
    }
    CORS(
        app,
        origins=["*"],
        allow_headers=["Content-Type"],
        methods=["GET", "POST", "PUT", "OPTIONS"],
    )
    app.register_api(new_lead_ogx)
    app.register_api(divisao_mercado)
    app.register_api_view(cadastro_lead_view)
    app.register_api(api)
    app.register_error_handler(AppError, handle_app_error)
    app.before_request(capture_request_start)
    app.before_request(verificar_origem)
    app.after_request(register_url)
    app.after_request(injetar_css_no_elements)
    app.logger.info("Aplicação de metadados B2C iniciada")

    # O Werkzeug inicia a aplicação duas vezes ao usar o reloader em DEV.
    # Pré-carrega apenas no processo filho que realmente atende as requisições.
    reloader_active: bool = (
        os.environ.get("WERKZEUG_RUN_MAIN", "").lower() == "true"
    )
    if not IS_DEV or reloader_active:
        try:
            async_to_sync(pre_carregamento_metadados)()
        except Exception:
            app.logger.exception("Falha no pré-carregamento dos metadados B2C")
    else:
        app.logger.info("Aguardando o processo do reloader para pré-carregar o cache")

    return app


__all__ = ["create_app"]
