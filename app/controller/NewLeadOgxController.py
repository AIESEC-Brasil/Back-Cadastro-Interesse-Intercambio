"""Endpoint de metadados do formulário B2C."""

from asgiref.sync import async_to_sync
from flask import jsonify

from ..cache import cache
from ..clients.b2c import enviar_metadados_b2c
from ..dto.output.metadadosDTO import Metadados
from ..router import Router

new_lead_ogx = Router(name="metadados_b2c", url_prefix="/new-lead-ogx")


@new_lead_ogx.get("/metadados", responses={200: Metadados})
def buscar_metadados():
    payload, status = async_to_sync(cache.get_or_set)(
        key="metadados_b2c",
        fetch=enviar_metadados_b2c,
    )
    response = jsonify(payload)
    response.headers["Content-Type"] = "application/json"
    return response, status


__all__ = ["new_lead_ogx"]
