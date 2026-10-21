"""DTOs destinados à persistência dos dados."""

from .lead import EmailPersistencia, LeadPersistencia, TelefonePersistencia

# ==============================================================================
# CONTRATOS DE PERSISTÊNCIA
# ==============================================================================
__all__ = ["EmailPersistencia", "LeadPersistencia", "TelefonePersistencia"]
