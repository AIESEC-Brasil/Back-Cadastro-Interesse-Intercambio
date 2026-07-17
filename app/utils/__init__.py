"""
Utils Module
------------

Ponto central de acesso para todos os utilitários da aplicação.
Este módulo agrupa funcionalidades de:
- Manipulação de Data/Hora (data)
- Segurança e Criptografia (crypto)
- Geração de E-mails (gerador)
- Formatação de Strings e URLs (formatar)
- Validações de Domínio (validates)
- Resolução de Respostas Async (resolve)
"""

# ==============================
# Importações Agregadas
# ==============================

# Importa todos os símbolos expostos em cada submódulo
from .data import *
from .formatar import *
from .validates import *
from .resolve import *
from .exception import *
from .gerador_sql import *
# ==============================
# Exportação Consolidada
# ==============================

# O __all__ define o que será exportado ao usar "from app.utils import *"
# Concatenamos as listas __all__ de cada submódulo para manter a consistência
__all__ =(
    data.__all__ +
    formatar.__all__ +
    validates.__all__ +
    resolve.__all__+
    exception.__all__+
    gerador_sql.__all__
)
