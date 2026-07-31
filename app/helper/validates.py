"""Helpers de validação específicos da camada de apresentação/regras de negócio.

Contém utilitários para verificação de limites de idade, formatos e regras
corporativas aplicadas ao recrutamento e elegibilidade de candidatos.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import re  # Biblioteca de Expressões Regulares para validação de padrões
from datetime import date, datetime  # Manipulação de datas e horários
from typing import Union  # Tipagem estática para suporte a múltiplos tipos


# =================================================================
# 2. VALIDAÇÕES DE FORMATO E REGRAS DE NEGÓCIO
# =================================================================

def tem_mais_de_31_anos(data_nascimento: Union[datetime, date, str]) -> bool:
    """Verifica se o candidato excede o limite de idade de 31 anos.

    Regra de negócio crítica para elegibilidade em programas com restrição de faixa etária.

    Args:
        data_nascimento (Union[datetime, date, str]): Objeto de data, data-hora
            ou string no formato ISO/banco ("%Y-%m-%d %H:%M:%S" ou "%Y-%m-%d").

    Returns:
        bool: True se a pessoa tiver mais de 30/31 anos completos. False caso contrário.
    """
    # 1. Normalização do tipo de entrada para objeto 'date'
    if isinstance(data_nascimento, datetime):
        nascimento = data_nascimento.date()
    elif isinstance(data_nascimento, str):
        try:
            # Tenta converter string com carimbo de data e hora (Timestamp)
            nascimento = datetime.strptime(
                data_nascimento, "%Y-%m-%d %H:%M:%S"
            ).date()
        except ValueError:
            # Fallback para string contendo apenas a data
            nascimento = datetime.strptime(data_nascimento, "%Y-%m-%d").date()
    else:
        # Assume que o objeto informado já seja do tipo 'date'
        nascimento = data_nascimento

    # Obtém a data atual do sistema
    hoje = date.today()

    # Cálculo base da diferença de anos
    idade = hoje.year - nascimento.year

    # Ajuste: subtrai 1 ano se o aniversário do ano corrente ainda não ocorreu
    if (hoje.month, hoje.day) < (nascimento.month, nascimento.day):
        idade -= 1

    # Retorna True se a idade for maior que 30 (ou seja, 31 anos ou mais completos)
    return idade >= 31


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = [
    "tem_mais_de_31_anos",
]