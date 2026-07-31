"""Módulo de Segurança: Decorator de Whitelist de IPs.

Protege rotas sensíveis garantindo que apenas requisições originadas de endereços
de IP previamente autorizados (ou em ambiente de desenvolvimento) possam executar
a lógica do endpoint.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from functools import wraps  # Preserva os metadados da função decorada
from typing import Any, Callable  # Tipagem estática para funções e retornos

from flask import jsonify, request  # Utilitários de requisição e JSON do Flask

from ..core import IS_DEV  # Flag indicativa do ambiente de desenvolvimento
from ..dto import HttpStatus  # Enúmero ou estrutura de códigos HTTP
from ..storage import storage  # Repositório/Singleton com a lista de IPs permitidos


# =================================================================
# 2. DECORATOR DE LIBERAÇÃO DE IP (WHITELIST)
# =================================================================

def require_ip_whitelist(
        func: Callable[..., Any]
) -> Callable[..., Any]:
    """Decorator que restringe o acesso a uma rota com base na Whitelist de IPs.

    Args:
        func (Callable[..., Any]): A função de controle da rota Flask.

    Returns:
        Callable[..., Any]: A função envelopada com a verificação de segurança.
    """

    @wraps(func)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # Carrega o conjunto (set) de IPs autorizados armazenados em memória (Complexidade O(1))
        allowed_ip_list = set(storage.get_ip())

        # Captura o IP retornado pelo proxy/load balancer ou direto da conexão física
        raw_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

        # Extrai o primeiro IP caso haja múltiplos proxies na cadeia (separados por vírgula)
        client_ip = raw_ip.split(",")[0].strip() if raw_ip else ""

        # Valida se o IP está autorizada ou se o sistema está em modo dev
        if client_ip not in allowed_ip_list and not IS_DEV:
            mensagem_erro = {
                "error": "Sua máquina não está autorizada a entrar nessa rota"
            }
            return jsonify(mensagem_erro), HttpStatus.UNAUTHORIZED

        # Executa a rota original se o IP for válido ou se IS_DEV for True
        return func(*args, **kwargs)

    return decorated_function


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["require_ip_whitelist"]