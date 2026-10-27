"""Integração externa necessária para buscar os metadados B2C."""

from .b2c import enviar_metadados_b2c

# ==============================================================================
# EXPORTAÇÕES DOS CLIENTES EXTERNOS
# ==============================================================================
__all__ = ["enviar_metadados_b2c"]
