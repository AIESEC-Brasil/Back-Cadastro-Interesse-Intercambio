"""Aplicação que disponibiliza somente os metadados do B2C."""

from flask_cors import CORS
from flask_openapi3 import Info, OpenAPI

from .api import api
from .controller import new_lead_ogx
from .core import setup_logging
from .middlewares import verificar_origem


def create_app() -> OpenAPI:
    setup_logging()
    app = OpenAPI(__name__, info=Info(title="Metadados B2C", version="1.0.0"))
    CORS(app, origins=["*"], allow_headers=["Content-Type"], methods=["GET", "OPTIONS"])
    app.register_api(new_lead_ogx)
    app.register_api(api)
    app.before_request(verificar_origem)
    app.logger.info("Aplicação de metadados B2C iniciada")
    return app


__all__ = ["create_app"]
