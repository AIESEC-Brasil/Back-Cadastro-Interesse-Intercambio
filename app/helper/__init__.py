"""Módulo de Exportação de Helpers (Helpers Package).

Ponto central de acesso para utilitários de validação e formatação.
Este pacote organiza funções auxiliares que dão suporte à lógica de
apresentação e integração com serviços externos (ex: Podio API).
"""

# =================================================================
# 1. IMPORTAÇÕES DE SUBMÓDULOS
# =================================================================

# Importação direta dos subpódulos para mapear as exportações
from . import formatar, validates

# Importações explícitas dos componentes para viabilizar acesso direto
from .formatar import *
from .validates import tem_mais_de_31_anos

# =================================================================
# 2. EXPORTAÇÃO CONSOLIDADA VIA __all__
# =================================================================

# O __all__ define a interface pública do pacote.
# Concatena as listas exportadas em 'validates' e 'formatar' para
# permitir importações diretas como: 'from app.helpers import tem_mais_de_31_anos'
__all__ = (
        validates.__all__ +
        formatar.__all__
)