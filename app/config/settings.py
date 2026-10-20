"""Configurações usadas pela rota de metadados B2C."""

import os


def _env(name: str, default: str | None = None) -> str:
    """Lê uma variável de ambiente obrigatória após remover espaços externos.

    Args:
        name: Nome da variável de ambiente.
        default: Valor usado quando a variável não está definida.

    Raises:
        ValueError: Quando o valor final estiver vazio.
    """
    value: str = os.getenv(name, default or "").strip()
    if not value:
        raise ValueError(f"Variável de ambiente obrigatória ausente: {name}")
    return value


AMBIENTE: str = _env("AMBIENTE", "PRODUCTION").upper()
CACHE_TTL: int = int(_env("CACHE_TTL", "3600"))
APPSCRIPT_B2C: str = _env("APPSCRIPT_B2C")
APPSCRIPT_DIVISAO_MERCADO: str = _env("APPSCRIPT_DIVISAO_MERCADO")
DOMINIOS_PERMITIDOS: list[str] = [
    domain.strip()
    for domain in _env("DOMINIOS_PERMITIDOS").split(",")
    if domain.strip()
]
API_KEYS_PERMITIDAS: list[str] = [
    key.strip()
    for key in os.getenv("API_KEYS_PERMITIDAS", "").split(",")
    if key.strip()
]

__all__ = [
    "AMBIENTE", "CACHE_TTL", "APPSCRIPT_B2C",
    "APPSCRIPT_DIVISAO_MERCADO",
    "DOMINIOS_PERMITIDOS", "API_KEYS_PERMITIDAS",
]
