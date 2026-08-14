"""Módulo de Rotas da Divisão de Mercado.

Define os endpoints para consulta de escritórios locais (CLs) e universidades
atrelados à divisão de mercado da organização, com suporte a cache.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import logging  # Sistema de log para rastreamento de operações e erros

from asgiref.sync import async_to_sync  # Adaptador para execução síncrona de corotinas

from ..cache import cache  # Gerenciador de cache para otimizar chamadas
from ..dto import (  # DTOs de validação e estruturação OpenAPI3/Pydantic
    DivisaoMercadoCl,
    DivisaoMercadoUniversidades,
    RetornoGenerico
)
from ..repository import (  # Métodos de consulta ao banco de dados/repositório
    buscar_todas_universidades,
    buscar_todos_cl,
)
from ..router import Router  # Classe estendida de roteamento OpenAPI3

# =================================================================
# 2. CONFIGURAÇÃO DO ROTEADOR E LOGGER
# =================================================================

# Instancia o roteador especializado para as rotas de Divisão de Mercado
divisao_mercado = Router(name="divisao_mercado", url_prefix="/divisao-mercado")

# Instancia o logger específico deste módulo
logger = logging.getLogger(__name__)


# =================================================================
# 3. ENDPOINTS E MANIPULADORES DE REQUISIÇÃO
# =================================================================

@divisao_mercado.get("/escritorios", responses={200: RetornoGenerico[DivisaoMercadoCl]})
def buscar_escritorios() -> DivisaoMercadoCl:
    """Retorna os dados da divisão de mercado por escritórios locais (CLs).

    Lógica de Cache:
    - Chave: 'divisao-mercado-escritorios'
    - Expiração: Segue o tempo de vida (TTL) global da aplicação.

    Returns:
        DivisaoMercadoCl: Estrutura contendo a lista de escritórios locais.
    """
    # Executa a corotina do cache de forma síncrona dentro do loop do Flask
    response, status = async_to_sync(cache.get_or_set)(
        key="divisao-mercado-escritorios",
        fetch=lambda: buscar_todos_cl(),
        baixando="Metadados da divisão de mercado por escritorio",
    )

    response.headers["Content-Type"] = "application/json"

    # Processa a lista de dados brutos para gerar a lista de objetos formatados
    dados_processados = DivisaoMercadoCl.processar_lista(
        cache.store["divisao-mercado-escritorios"]["data"]
    )

    # Instancia o DTO com os dados processados e exporta como dicionário/modelo
    return DivisaoMercadoCl(cl=dados_processados).model_dump()


@divisao_mercado.get(
    "/universidades", responses={200: RetornoGenerico[DivisaoMercadoUniversidades]}
)
def buscar_universidades() -> DivisaoMercadoUniversidades:
    """Retorna os dados da divisão de mercado agrupados por universidades.

    Lógica de Cache:
    - Chave: 'divisao-mercado-universidades'
    - Expiração: Segue o tempo de vida (TTL) global da aplicação.

    Returns:
        DivisaoMercadoUniversidades: DTO contendo a lista de universidades mapeadas.
    """
    # Executa a corotina do cache de forma síncrona dentro do loop do Flask
    response, status = async_to_sync(cache.get_or_set)(
        key="divisao-mercado-universidades",
        fetch=lambda: buscar_todas_universidades(),
        baixando="Metadados da divisão de mercado por Universidades",
    )

    response.headers["Content-Type"] = "application/json"

    # Processa a lista de dados brutos para gerar a lista de universidades
    dados_processados = DivisaoMercadoUniversidades.processar_lista(
        cache.store["divisao-mercado-universidades"]["data"]
    )

    # Instancia o DTO passando a lista processada e exporta como dicionário
    return DivisaoMercadoUniversidades(
        universidades=dados_processados
    ).model_dump()


# =================================================================
# 4. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = [
    "divisao_mercado",  # Roteador consolidado das rotas da divisão de mercado
]