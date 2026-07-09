"""
Helpers Module
--------------

Ponto central de acesso para utilitários de validação e formatação.
Este pacote organiza funções auxiliares que dão suporte à lógica de
apresentação e integração com serviços externos.
"""

# ==============================
# Importações de Submódulos
# ==============================

# Importa todas as validações de regras de negócio (idade, e-mail, membresia)
from .validates import *

# Importa todos os formatadores de strings e URLs de integração
from .formatar import *

# ==============================
# Exportação Consolidada
# ==============================

#

# O __all__ define a interface pública do pacote.
# Concatenamos as listas exportadas em 'validates' e 'formatar' para
# permitir importações diretas como: 'from app.helpers import tem_mais_de_31_anos'
__all__ = (
    validates.__all__ +
    formatar.__all__
)