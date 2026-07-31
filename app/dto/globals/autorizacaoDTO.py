from enum import (
    IntEnum,          # Variante de enumerador onde os membros são comparáveis a inteiros, ideal para flags numéricas.
)

class Autorizacao(IntEnum):
    """
    Enumeração para representação binária de estados de consentimento e autorização.

    Esta classe utiliza IntEnum para garantir que os valores internos sejam estritamente
    inteiros (0 ou 1), facilitando a persistência limpa e direta em APIs de terceiros
    (como o ecossistema do Podio) e em bancos de dados que interpretam flags numéricas.

    Members:
        SIM (int): Indica consentimento e autorização explicitamente concedidos (1).
        NAO (int): Indica consentimento ou autorização expressamente negados/revogados (0).
    """
    SIM = 1  # Valor inteiro representando autorização concedida
    NAO = 0  # Valor inteiro representando autorização negada

__all__ = ["Autorizacao"]