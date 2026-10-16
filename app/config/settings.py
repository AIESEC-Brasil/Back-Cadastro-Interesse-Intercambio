"""Configurações usadas pela rota de metadados B2C."""

import os

def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default or "").strip()
    if not value:
        raise ValueError(f"Variável de ambiente obrigatória ausente: {name}")
    return value


AMBIENTE = _env("AMBIENTE", "PRODUCTION").upper()
CACHE_TTL = int(_env("CACHE_TTL", "3600"))
APPSCRIPT_B2C = _env("APPSCRIPT_B2C")
DOMINIOS_PERMITIDOS = [
    domain.strip()
    for domain in _env("DOMINIOS_PERMITIDOS").split(",")
    if domain.strip()
]
API_KEYS_PERMITIDAS = [
    key.strip()
    for key in os.getenv("API_KEYS_PERMITIDAS", "").split(",")
    if key.strip()
]

__all__ = [
    "AMBIENTE", "CACHE_TTL", "APPSCRIPT_B2C",
    "DOMINIOS_PERMITIDOS", "API_KEYS_PERMITIDAS",
]
