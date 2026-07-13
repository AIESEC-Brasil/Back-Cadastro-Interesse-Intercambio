from functools import wraps
from flask import request, jsonify
from ..dto import HttpStatus
from ..storage import storage

def require_ip_whitelist(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # A lógica que antes estava no middleware grande
        allowed_ip_list = set(storage.get_ip())
        
        # Pega o primeiro IP (evita problemas com múltiplos proxies)
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        if client_ip not in allowed_ip_list:
            return jsonify({"error": "Sua máquina não está autorizada a entrar nessa rota"}), HttpStatus.UNAUTHORIZED
        
        return func(*args, **kwargs)
    return decorated_function

__all__ = [
    "require_ip_whitelist"
]