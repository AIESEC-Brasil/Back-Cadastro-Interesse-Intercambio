"""Aplicação que disponibiliza somente os metadados do B2C."""

from flask_cors import CORS
from flask_openapi3 import Info, OpenAPI

from .controller import new_lead_ogx


def create_app() -> OpenAPI:
    app = OpenAPI(__name__, info=Info(title="Metadados B2C", version="1.0.0"))
    CORS(app, origins=["*"], allow_headers=["Content-Type"], methods=["GET", "OPTIONS"])
    app.register_api(new_lead_ogx)
    return app


__all__ = ["create_app"]
