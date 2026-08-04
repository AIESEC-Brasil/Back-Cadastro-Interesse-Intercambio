"""Módulo de repositório e consultas assíncronas de Divisão de Mercado.

Utiliza `asyncio.to_thread` para encapsular operações de I/O bloqueantes do SQLAlchemy
(módulo ORM síncrono da aplicação) em threads separadas, mantendo assinaturas
assíncronas puras para integração transparente com caches, pipelines e middlewares.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import asyncio  # Gerenciamento de assincronismo e thread-pools no Python
from typing import Any, Dict, List, Optional  # Tipagem estática para estruturas de dados

from sqlalchemy import select  # Construtor de queries SQL unificadas do SQLAlchemy

from ..core import db  # Instância global da extensão SQLAlchemy do Flask
from ..model import DivisaoCL, Universidades  # Modelos ORM das tabelas do banco
from ..schema import (
    divisao_universidades_schema,      # Schema Marshmallow para um único registro de universidade
    divisoes_cl_schema,               # Schema Marshmallow para múltiplos registros de CLs
    divisoes_universidades_schema,    # Schema Marshmallow para múltiplos registros de universidades
)


# =================================================================
# 2. CONSULTAS DE UNIVERSIDADES
# =================================================================

def _executar_buscar_todas_universidades() -> List[Dict[str, Any]]:
    """Executa a consulta síncrona no banco de dados para buscar todas as universidades.

    Esta função bloqueante é projetada para ser executada em background dentro de uma thread.

    Returns:
        List[Dict[str, Any]]: Lista de dicionários serializados contendo as universidades.
    """
    # Constrói a instrução SQL de seleção da tabela Universidades
    instrucao = select(Universidades)

    # Executa a query dentro da sessão ativa do SQLAlchemy
    resultado = db.session.execute(instrucao)

    # Obtém todos os objetos ORM retornados
    registros = resultado.scalars().all()

    # Serializa os objetos em uma lista de dicionários via Marshmallow
    return divisoes_universidades_schema.dump(registros)


async def buscar_todas_universidades() -> List[Dict[str, Any]]:
    """Busca todas as universidades de forma assíncrona executando I/O em thread delegada.

    Returns:
        List[Dict[str, Any]]: Lista de dicionários representando as universidades registradas.
    """
    # Delega a execução da função bloqueante para o pool de threads
    return await asyncio.to_thread(_executar_buscar_todas_universidades)


def _executar_buscar_universidade_por_id(id_universidade: int) -> Optional[Dict[str, Any]]:
    """Executa a consulta síncrona no banco para buscar uma universidade específica por ID.

    Args:
        id_universidade (int): ID identificador da universidade no banco.

    Returns:
        Optional[Dict[str, Any]]: Dicionário da universidade encontrada ou None.
    """
    # Monta a query filtrando pelo campo ID
    instrucao = select(Universidades).where(Universidades.id == id_universidade)

    # Executa a busca na sessão do banco
    resultado = db.session.execute(instrucao)

    # Extrai o primeiro registro retornado ou None se não encontrar
    registro = resultado.scalar_one_or_none()

    # Serializa e retorna o dicionário do registro caso exista
    return divisao_universidades_schema.dump(registro) if registro else None


async def buscar_universidade_por_id(id_universidade: int) -> Optional[Dict[str, Any]]:
    """Busca uma universidade pelo seu ID de forma assíncrona.

    Args:
        id_universidade (int): ID da universidade desejada.

    Returns:
        Optional[Dict[str, Any]]: Dicionário contendo os dados da universidade ou None.
    """
    # Passa o parâmetro id_universidade junto com a função síncrona para a thread
    return await asyncio.to_thread(_executar_buscar_universidade_por_id, id_universidade)


def _executar_buscar_universidade_por_nome(nome_universidade: str) -> Optional[Dict[str, Any]]:
    """Executa a consulta síncrona no banco para buscar uma universidade por Nome exacto.

    Args:
        nome_universidade (str): Nome textual exato da universidade.

    Returns:
        Optional[Dict[str, Any]]: Dicionário da universidade encontrada ou None.
    """
    # Monta a query filtrando estritamente pelo campo Nome
    instrucao = select(Universidades).where(Universidades.nome == nome_universidade)

    # Executa a busca na sessão
    resultado = db.session.execute(instrucao)

    # Retorna um único registro ou None
    registro = resultado.scalar_one_or_none()

    # Converte para dicionário serializado
    return divisao_universidades_schema.dump(registro) if registro else None


async def buscar_universidade_por_nome(nome_universidade: str) -> Optional[Dict[str, Any]]:
    """Busca uma universidade pelo seu Nome de forma assíncrona.

    Args:
        nome_universidade (str): Nome da universidade a ser pesquisada.

    Returns:
        Optional[Dict[str, Any]]: Dicionário contendo os dados da universidade ou None.
    """
    # Delega a busca por nome para uma thread separada
    return await asyncio.to_thread(_executar_buscar_universidade_por_nome, nome_universidade)


# =================================================================
# 3. CONSULTAS DE ESCRITÓRIOS LOCAIS (CLs)
# =================================================================

def _executar_buscar_todos_cl() -> List[Dict[str, Any]]:
    """Executa a consulta síncrona no banco de dados para buscar todos os CLs.

    Esta função bloqueante é projetada para ser executada em background dentro de uma thread.

    Returns:
        List[Dict[str, Any]]: Lista de dicionários serializados contendo os CLs.
    """
    # Prepara a seleção de todos os comitês/escritórios locais
    instrucao = select(DivisaoCL)

    # Executa no banco
    resultado = db.session.execute(instrucao)

    # Recupera todos os objetos encontrados
    registros = resultado.scalars().all()

    # Serializa no schema de CLs
    return divisoes_cl_schema.dump(registros)


async def buscar_todos_cl() -> List[Dict[str, Any]]:
    """Busca todos os escritórios locais (CLs) de forma assíncrona.

    Returns:
        List[Dict[str, Any]]: Lista de dicionários representando os CLs registrados.
    """
    # Encapsula a chamada síncrona na thread
    return await asyncio.to_thread(_executar_buscar_todos_cl)


# =================================================================
# 4. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = [
    "buscar_todas_universidades",
    "buscar_universidade_por_id",
    "buscar_universidade_por_nome",
    "buscar_todos_cl",
]