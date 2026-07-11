from app.core import db
from app.model import Universidades, DivisaoCL

def buscar_todas_universidades():
    """
    Retorna todos os registros da tabela Universidades.

    Returns:
        list: Lista de objetos Universidades.
    """
    return Universidades.query.all()

def buscar_todos_cl():
    """
    Retorna todos os registros da tabela DivisaoCL.

    Returns:
        list: Lista de objetos DivisaoCL.
    """
    return DivisaoCL.query.all()

__all__ = [
    "buscar_todas_universidades",
    "buscar_todos_cl"
]