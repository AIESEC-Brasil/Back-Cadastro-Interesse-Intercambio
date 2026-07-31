"""Módulo de repositório e consultas assíncronas de Divisão de Mercado.

Utiliza `asyncio.to_thread` para encapsular operações de I/O bloqueantes do SQLAlchemy
(módulo ORM síncrono da aplicação) em threads separadas, mantendo assinaturas
assíncronas puras para integração transparente com caches, pipelines e middlewares.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import asyncio  # Gerenciamento de assincronismo e thread-pools no Python
from typing import Any, Dict, List  # Tipagem estática para estruturas de dados

from sqlalchemy import select  # Construtor de queries SQL unificadas do SQLAlchemy

from ..core import db  # Instância global da extensão SQLAlchemy do Flask
from ..model import DivisaoCL, Universidades  # Modelos ORM das tabelas
from ..schema import divisoes_cl_schema, divisoes_universidades_schema  # Schemas Marshmallow


# =================================================================
# 2. CONSULTAS DE UNIVERSIDADES
# =================================================================

def _executar_buscar_todas_universidades() -> List[Dict[str, Any]]:
    """Executa a consulta síncrona no banco de dados para buscar todas as universidades.

    Esta função bloqueante é projetada para ser executada em background dentro de uma thread.

    Returns:
        List[Dict[str, Any]]: Lista de dicionários serializados contendo as universidades.
    """
    instrucao = select(Universidades)
    resultado = db.session.execute(instrucao)
    registros = resultado.scalars().all()
    return divisoes_universidades_schema.dump(registros)


async def buscar_todas_universidades() -> List[Dict[str, Any]]:
    """Busca todas as universidades de forma assíncrona executando I/O em thread delegada.

    Returns:
        List[Dict[str, Any]]: Lista de dicionários representando as universidades registradas.
    """
    return await asyncio.to_thread(_executar_buscar_todas_universidades)


# =================================================================
# 3. CONSULTAS DE ESCRITÓRIOS LOCAIS (CLs)
# =================================================================

def _executar_buscar_todos_cl() -> List[Dict[str, Any]]:
    """Executa a consulta síncrona no banco de dados para buscar todos os CLs.

    Esta função bloqueante é projetada para ser executada em background dentro de uma thread.

    Returns:
        List[Dict[str, Any]]: Lista de dicionários serializados contendo os CLs.
    """
    instrucao = select(DivisaoCL)
    resultado = db.session.execute(instrucao)
    registros = resultado.scalars().all()
    return divisoes_cl_schema.dump(registros)


async def buscar_todos_cl() -> List[Dict[str, Any]]:
    """Busca todos os escritórios locais (CLs) de forma assíncrona.

    Returns:
        List[Dict[str, Any]]: Lista de dicionários representando os CLs registrados.
    """
    return await asyncio.to_thread(_executar_buscar_todos_cl)


# =================================================================
# 4. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = [
    "buscar_todas_universidades",
    "buscar_todos_cl",
]