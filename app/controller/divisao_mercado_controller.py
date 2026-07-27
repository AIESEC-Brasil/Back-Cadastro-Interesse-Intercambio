"""
Lead B2C (OGX) Routes
---------------------

Define os endpoints para captação de leads interessados em intercâmbios (B2C).
Gerencia metadados estruturais do Podio e o fluxo de inscrição para OGX.
"""

# ==============================
# Importações (Dependencies)
# ==============================
import logging  # Sistema de log para rastreamento de performance e erros
from asgiref.sync import async_to_sync
from ..router import Router  # Classe base de roteamento integrada ao OpenAPI3
from ..cache import cache  # Gerenciador de cache para otimizar chamadas de API
from ..dto import DivisaoMercadoUniversidades, DivisaoMercadoCl  # DTOs específicos para cada rota
from ..repository import buscar_todas_universidades, buscar_todos_cl

# =================================================================
# CONFIGURAÇÃO DO ROTEADOR OGX
# =================================================================

# Instancia o roteador especializado.
divisao_mercado = Router(name="divisao_mercadao", url_prefix="/divisao-mercado")

# =================================================================
# CONFIGURAÇÃO DE LOGGING
# =================================================================

# Instancia o logger para este módulo, permitindo rastrear eventos e erros.
logger = logging.getLogger(__name__)


# =================================================================
# ENDPOINTS (ROTAS)
# =================================================================

@divisao_mercado.get("/escritorios", responses={200: DivisaoMercadoCl})
def buscar_escritorios() -> DivisaoMercadoCl:
    """
    Retorna a estrutura de campos do App de Leads B2C do Podio.

    Lógica de Cache:
    - Chave: 'divisao-mercado-escritorios'
    - Autenticação: Utiliza o token específico de OGX ('ogx-token-podio')
    - Expiração: Segue o CACHE_TTL global.
    """
    # Executa a corotina de forma síncrona e segura, aproveitando o loop do Flask
    # sem disparar o erro do validador do Pydantic / OpenAPI3
    response, status = async_to_sync(cache.get_or_set)(
        key="divisao-mercado-escritorios",
        fetch=lambda: buscar_todos_cl(),
        baixando="Metadados da divisão de mercado por escritorio"
    )

    response.headers["Content-Type"] = "application/json"

    # Processa a lista de dados brutos para gerar a lista de objetos DivisaoMercado
    dados_processados = DivisaoMercadoCl.processar_lista(cache.store["divisao-mercado-escritorios"]["data"])

    # Instancia o DTO passando a lista processada no atributo 'cl' e exporta como dicionário
    return DivisaoMercadoCl(cl=dados_processados).model_dump()


@divisao_mercado.get("/universidades", responses={200: DivisaoMercadoUniversidades})
def buscar_universidades() -> DivisaoMercadoUniversidades:
    """
    Retorna a estrutura de campos do App de Leads B2C do Podio.

    Lógica de Cache:
    - Chave: 'divisao-mercado-universidades'
    - Autenticação: Utiliza o token específico de OGX ('ogx-token-podio')
    - Expiração: Segue o CACHE_TTL global.
    """
    # Executa a corotina de forma síncrona e segura, aproveitando o loop do Flask
    # sem disparar o erro do validador do Pydantic / OpenAPI3
    response, status = async_to_sync(cache.get_or_set)(
        key="divisao-mercado-universidades",
        fetch=lambda: buscar_todas_universidades(),
        baixando="Metadados da divisão de mercado por Universidades"
    )

    response.headers["Content-Type"] = "application/json"

    # Processa a lista de dados brutos para gerar a lista de objetos DivisaoMercado
    dados_processados = DivisaoMercadoUniversidades.processar_lista(cache.store["divisao-mercado-universidades"]["data"])

    # Instancia o DTO passando a lista processada no atributo 'universidades' e exporta como dicionário
    return DivisaoMercadoUniversidades(universidades=dados_processados).model_dump()


# ==============================
# Exportações do Módulo
# ==============================
__all__ = [
    "divisao_mercado"
]