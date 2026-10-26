"""DTOs destinados à persistência dos dados."""

from .lead import (
    EmailPersistencia,
    LeadPersistencia,
    QualificacaoPersistencia,
    TelefonePersistencia,
)

# ==============================================================================
# CONTRATOS DE PERSISTÊNCIA
# ==============================================================================
__all__ = [
    "EmailPersistencia",
    "LeadPersistencia",
    "QualificacaoPersistencia",
    "TelefonePersistencia",
]
