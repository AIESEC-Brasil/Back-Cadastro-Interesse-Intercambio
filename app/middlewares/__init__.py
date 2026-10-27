"""Middleware necessário para proteger a documentação da API."""

from .lista_autorizados import require_ip_whitelist
from .autorizacao import verificar_origem
from .registrando_endpoint import capture_request_start, register_url
from .elements_css import injetar_css_no_elements

# ==============================================================================
# MIDDLEWARES PÚBLICOS DA APLICAÇÃO
# ==============================================================================
__all__ = [
    "require_ip_whitelist",
    "verificar_origem",
    "capture_request_start",
    "register_url",
    "injetar_css_no_elements",
]
