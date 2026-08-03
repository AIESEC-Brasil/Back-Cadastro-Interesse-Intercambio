"""Módulo de Rotas de Leads B2C (OGX).

Define os endpoints para captação de leads interessados em intercâmbios (B2C).
Gerencia metadados estruturais do Podio e o fluxo de inscrição/pré-cadastro.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import logging  # Sistema de log para rastreamento de operações e erros

from asgiref.sync import async_to_sync  # Adaptador para execução síncrona de corotinas

from ..cache import cache  # Gerenciador de cache da aplicação
from ..clients import metadados  # Cliente HTTP para metadados da API do Podio
from ..config import APP_ID  # ID do aplicativo Podio para Leads OGX
from ..dto import (  # DTOs de validação e serialização OpenAPI3/Pydantic
    ConflitosLeadOutput,
    CriarPreCadastroLead,
    LeadPreCadastroOutput,
    Metadados,
)
from ..middlewares import gerar_token_podio_rota  # Interceptador de autenticação de rota
from ..router import Router  # Classe estendida de roteamento OpenAPI3
from ..service import cadastrar_lead  # Regra de negócio para criação de leads

# =================================================================
# 2. CONFIGURAÇÃO DO ROTEADOR E LOGGER
# =================================================================

# Instancia o roteador especializado para a rota /new-lead-ogx
new_lead_ogx = Router(name="novos_leads_ogx", url_prefix="/new-lead-ogx")

# Instancia o logger específico deste módulo
logger = logging.getLogger(__name__)


# =================================================================
# 3. ENDPOINTS E MANIPULADORES DE REQUISIÇÃO
# =================================================================

@new_lead_ogx.get("/metadados", responses={200: Metadados})
@gerar_token_podio_rota(service="new-lead-ogx")
def buscar_metadados() -> Metadados:
    """Retorna a estrutura de campos do App de Leads B2C do Podio.

    Lógica de Cache:
    - Chave: 'metadados_card-ogx'
    - Autenticação: Utiliza o token específico de OGX ('ogx-token-podio')
    - Expiração: Segue o tempo de vida (TTL) configurado na aplicação.

    Returns:
        Metadados: Estrutura dos campos do aplicativo Podio serializada.
    """
    # Executa a corotina do cache de forma síncrona dentro do loop do Flask
    response, status = async_to_sync(cache.get_or_set)(
        key="metadados_card-ogx",
        fetch=lambda: metadados(
            chave="ogx-token-podio",
            app_id=APP_ID,
        ),
        baixando="Metadados de Novos lead B2C",
    )

    response.headers["Content-Type"] = "application/json"

    # Converte os dados salvos no cache para a instância do modelo Pydantic/DTO
    return Metadados(**cache.store["metadados_card-ogx"]).model_dump()


@new_lead_ogx.post(
    "/cadastro",
    responses={
        201: LeadPreCadastroOutput,
        200: LeadPreCadastroOutput,
        409: ConflitosLeadOutput,
    },
)
@gerar_token_podio_rota(service="new-lead-ogx")
def criar_inscricao(body: CriarPreCadastroLead):
    """Endpoint para recepção e processamento de novos leads de intercâmbio.

    Args:
        body (CriarPreCadastroLead): DTO validado contendo os dados do candidato.

    Returns:
        Response: Objeto de resposta processado pela camada de serviço.
    """
    logger.info("AIESEC OGX | Iniciando processo de cadastro de novo lead...")

    # Delega o processamento da regra de negócio para a camada de serviço
    return cadastrar_lead(body)


# =================================================================
# 4. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = [
    "new_lead_ogx",  # Roteador consolidado das rotas de Leads OGX B2C
]