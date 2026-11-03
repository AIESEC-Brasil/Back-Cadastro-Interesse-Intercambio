"""Estratégias intercambiáveis para fluxos de negócio."""

from .lead_registration import (
    B2CLeadPersistenceStrategy,
    ExpaLeadPersistenceStrategy,
    LeadPersistenceStrategy,
)

__all__ = [
    "B2CLeadPersistenceStrategy",
    "ExpaLeadPersistenceStrategy",
    "LeadPersistenceStrategy",
]
