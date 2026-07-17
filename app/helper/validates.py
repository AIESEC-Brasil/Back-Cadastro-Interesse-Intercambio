"""
Helpers de validação específicos da camada de apresentação/regras de negócio.
"""

# ==============================
# Importações (Dependencies)
# ==============================
import re                           # Biblioteca de Expressões Regulares para validação de padrões
from ..globals import List, date, datetime # Tipagem e objetos de manipulação de data/tempo

# ==============================
# Validações de Formato e Regras
# ==============================
def tem_mais_de_31_anos(data_nascimento: datetime | str) -> bool:
    """
    Verifica se o candidato atende ao critério de idade (limite: 31 anos).

    Esta é uma regra crítica para programas de intercâmbio ou voluntariado
    jovem que possuem restrição de faixa etária.



    Args:
        data_nascimento (datetime | str): Objeto de data ou string formatada.

    Returns:
        bool: True se a pessoa tiver 31 anos ou menos. False se tiver 32 ou mais.
    """
    # 1. Normalização da entrada para o tipo 'date'
    if isinstance(data_nascimento, datetime):
        nascimento = data_nascimento.date()
    elif isinstance(data_nascimento, str):
        # Converte a string considerando o formato padrão de timestamp do banco/API
        nascimento = datetime.strptime(data_nascimento, "%Y-%m-%d %H:%M:%S").date()
    else:
        nascimento = data_nascimento  # Assume que o objeto já é do tipo 'date'

    hoje = date.today()

    # Cálculo base pela diferença de anos
    idade = hoje.year - nascimento.year

    # Ajuste fino: Se o mês/dia atual for menor que o de nascimento,
    # significa que a pessoa ainda não fez aniversário este ano.
    if (hoje.month, hoje.day) < (nascimento.month, nascimento.day):
        idade -= 1

    # Retorna True se estiver dentro do limite (<= 31)
    return not (idade >= 31)

# ==============================
# Exportações
# ==============================
__all__ = [
    "tem_mais_de_31_anos",
]