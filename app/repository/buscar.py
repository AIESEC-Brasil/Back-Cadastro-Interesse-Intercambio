from ..core import db
from ..model import Universidades, DivisaoCL
from ..schema import divisoes_Universidades_schema, divisoes_CL_schema

def buscar_todas_universidades():
    """
    Retorna todos os registros da tabela Universidades.

    Returns:
        list: Lista de objetos Universidades.
    """
    return divisoes_Universidades_schema.dump(Universidades.query.all())

def buscar_todos_cl():
    """
    Retorna todos os registros da tabela DivisaoCL.

    Returns:
        list: Lista de objetos DivisaoCL.
    """
    return divisoes_CL_schema.dump(DivisaoCL.query.all())

__all__ = [
    "buscar_todas_universidades",
    "buscar_todos_cl"
]