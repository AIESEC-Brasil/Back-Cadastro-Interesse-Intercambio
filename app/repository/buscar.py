from typing import List, Dict, Any
from sqlalchemy import select  # Essencial para queries assíncronas no SQLAlchemy moderno
from ..core import db
from ..model import Universidades, DivisaoCL
from ..schema import divisoes_Universidades_schema, divisoes_CL_schema

async def buscar_todas_universidades() -> List[Dict[str, Any]]:
    """
    Recupera e serializa todos os registros da tabela de Universidades de forma assíncrona.

    Utiliza a API moderna 'select' do SQLAlchemy para garantir compatibilidade
    com sessões assíncronas (AsyncSession), evitando o bloqueio da thread principal.

    Returns:
        List[Dict[str, Any]]: Lista de dicionários representando as universidades,
        serializadas conforme o esquema `divisoes_Universidades_schema`.

    Raises:
        SQLAlchemyError: Se ocorrer um erro de conexão ou execução da query assíncrona.
    """
    # Criamos a instrução SQL abstrata (padrão SQLAlchemy 2.0)
    instrucao = select(Universidades)

    # Executamos de forma assíncrona com 'await', liberando a CPU durante a espera do banco
    resultado = await db.session.execute(instrucao)

    # Extraímos os objetos do resultado retornado
    registros = resultado.scalars().all()

    # Serialização em memória (operação síncrona executada após a resposta do banco)
    return divisoes_Universidades_schema.dump(registros)


async def buscar_todos_cl() -> List[Dict[str, Any]]:
    """
    Recupera e serializa todos os registros de Divisão CL de forma assíncrona.

    Utiliza select() e execução assíncrona para não bloquear o event loop
    do servidor durante a consulta à tabela 'DivisaoCL'.

    Returns:
        List[Dict[str, Any]]: Lista de dicionários com as divisões CL,
        serializadas conforme `divisoes_CL_schema`.

    Raises:
        SQLAlchemyError: Se a consulta assíncrona falhar.
    """
    instrucao = select(DivisaoCL)
    resultado = await db.session.execute(instrucao)
    registros = resultado.scalars().all()

    return divisoes_CL_schema.dump(registros)


__all__ = [
    "buscar_todas_universidades",
    "buscar_todos_cl"
]