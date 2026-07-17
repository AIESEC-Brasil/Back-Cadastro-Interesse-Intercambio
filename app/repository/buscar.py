import asyncio
from typing import List, Dict, Any
from sqlalchemy import select
from ..core import db
from ..model import Universidades, DivisaoCL
from ..schema import divisoes_Universidades_schema, divisoes_CL_schema

def _executar_buscar_todas_universidades() -> List[Dict[str, Any]]:
    # Código síncrono que roda na thread separada
    instrucao = select(Universidades)
    resultado = db.session.execute(instrucao)
    registros = resultado.scalars().all()
    return divisoes_Universidades_schema.dump(registros)

async def buscar_todas_universidades() -> List[Dict[str, Any]]:
    """
    Função assíncrona que executa a query síncrona em uma thread em background.
    Mantém a assinatura assíncrona pura para o seu cache e middlewares.
    """
    return await asyncio.to_thread(_executar_buscar_todas_universidades)


def _executar_buscar_todos_cl() -> List[Dict[str, Any]]:
    # Código síncrono que roda na thread separada
    instrucao = select(DivisaoCL)
    resultado = db.session.execute(instrucao)
    registros = resultado.scalars().all()
    return divisoes_CL_schema.dump(registros)

async def buscar_todos_cl() -> List[Dict[str, Any]]:
    """
    Função assíncrona que executa a query síncrona em uma thread em background.
    Mantém a assinatura assíncrona pura para o seu cache e middlewares.
    """
    return await asyncio.to_thread(_executar_buscar_todos_cl)


__all__ = [
    "buscar_todas_universidades",
    "buscar_todos_cl"
]