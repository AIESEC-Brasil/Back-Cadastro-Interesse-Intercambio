"""Módulo de Enumeração para Estados de Autorização.

Este módulo define o enumerador `Autorizacao`, responsável por representar
de forma binária/numérica (0 ou 1) os estados de consentimento e aceite dos leads,
garantindo compatibilidade nativa com APIs de terceiros (como o Podio) e bancos de dados.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from enum import IntEnum  # Variante de enumerador cujos membros são inteiros comparáveis e serializáveis.


# =================================================================
# 2. ENUMERADOR DE AUTORIZAÇÃO / CONSENTIMENTO
# =================================================================

class Autorizacao(IntEnum):
    """Enumeração para representação binária de estados de consentimento e autorização.

    Esta classe utiliza IntEnum para garantir que os valores internos sejam estritamente
    inteiros (0 ou 1), facilitando a persistência limpa e direta em APIs de terceiros
    (como o ecossistema do Podio) e em bancos de dados que interpretam flags numéricas.

    Members:
        SIM (int): Indica consentimento e autorização explicitamente concedidos (1).
        NAO (int): Indica consentimento ou autorização expressamente negados/revogados (0).
    """

    SIM = 1  # Valor inteiro representando autorização concedida
    NAO = 0  # Valor inteiro representando autorização negada


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["Autorizacao"]