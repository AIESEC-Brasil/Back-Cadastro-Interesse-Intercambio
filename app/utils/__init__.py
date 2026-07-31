"""Módulo Central de Utilitários (Utils Package).

Ponto central de exportação e agregador para todos os submódulos da aplicação.

Agrupa funcionalidades de:
- Manipulação e fuso horário de Data/Hora (data)
- Formatação de nomes e URLs (formatar)
- Validações de domínio e credenciais (validates)
- Resolução e normalização de operações assíncronas (resolve)
- Trata exceções e middleware para validações OpenAPI3 (exception)
- Geração automatizada de seeds SQL a partir de JSON (gerador_sql)
"""

# =================================================================
# 1. IMPORTAÇÕES AGREGADAS DOS SUBMÓDULOS
# =================================================================
from . import data, exception, formatar, gerador_sql, resolve, validates
from .data import *
from .exception import *
from .formatar import *
from .gerador_sql import *
from .resolve import *
from .validates import *

# =================================================================
# 2. EXPORTAÇÃO CONSOLIDADA VIA __all__
# =================================================================

# Concatena dinamicamente os símbolos expostos no __all__ de cada submódulo
__all__ = (
        data.__all__
        + formatar.__all__
        + validates.__all__
        + resolve.__all__
        + exception.__all__
        + gerador_sql.__all__
)