"""Middleware necessário para proteger a documentação da API."""

from .lista_autorizados import require_ip_whitelist
from .autorizacao import verificar_origem

__all__ = ["require_ip_whitelist", "verificar_origem"]
