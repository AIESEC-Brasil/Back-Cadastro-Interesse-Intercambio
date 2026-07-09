from flask import jsonify, make_response
from .resolve import resolve_exception


def handle_validation_error(e):

    # 1. Resolve o erro usando sua lógica
    erro_resolvido = resolve_exception(e)

    # 2. Em vez de retornar (dict, int), crie uma resposta Flask real
    response_body = erro_resolvido.model_dump()
    status_code = erro_resolvido.status_code

    # O segredo é o jsonify aqui para o abort() do OpenAPI3 não engasgar
    return make_response(jsonify(response_body), status_code)


__all__ = ["handle_validation_error"]