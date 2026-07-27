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
from ..config import APP_ID  # ID do App de Leads B2C no Podio (configurado no .env)
from ..clients import metadados  # Função cliente para buscar campos e configurações do Podio
from ..dto import Metadados,LeadPreCadastroInput  # DTO para validação e serialização de metadados do Podio
from ..middlewares import gerar_token_podio_rota  # Funções de interceptação
from ..service import cadastrar_lead

# =================================================================
# CONFIGURAÇÃO DO ROTEADOR OGX
# =================================================================

# Instancia o roteador especializado.
new_lead_ogx = Router(name="novos_leads_ogx", url_prefix="/new-lead-ogx")

# =================================================================
# CONFIGURAÇÃO DE LOGGING
# =================================================================

# Instancia o logger para este módulo, permitindo rastrear eventos e erros.
logger = logging.getLogger(__name__)


# =================================================================
# ENDPOINTS (ROTAS)
# =================================================================

@new_lead_ogx.get("/metadados", responses={200: Metadados})
@gerar_token_podio_rota(service="new-lead-ogx")
def buscar_metadados() -> Metadados:
    """
    Retorna a estrutura de campos do App de Leads B2C do Podio.

    Lógica de Cache:
    - Chave: 'metadados_card-ogx'
    - Autenticação: Utiliza o token específico de OGX ('ogx-token-podio')
    - Expiração: Segue o CACHE_TTL global.
    """
    # Executa a corotina de forma síncrona e segura, aproveitando o loop do Flask
    # sem disparar o erro do validador do Pydantic / OpenAPI3
    response, status = async_to_sync(cache.get_or_set)(
        key="metadados_card-ogx",
        fetch=lambda: metadados(
            chave="ogx-token-podio",
            APP_ID=APP_ID
        ),
        baixando="Metadados de Novos lead B2C"
    )

    response.headers["Content-Type"] = "application/json"

    # Retorna o dicionário limpo. O Flask-OpenAPI3 agora receberá o dict
    # e validará com sucesso usando o Pydantic!
    return Metadados(**cache.store["metadados_card-ogx"]).model_dump()


@new_lead_ogx.post("/cadastro")
@gerar_token_podio_rota(service="new-lead-ogx")
def criar_incricao(body:LeadPreCadastroInput):
    """
    Endpoint para recepção de novos leads de intercâmbio.

    Por ser um cadastro, força o resync do cache para que a próxima chamada
    à rota de metadados busque dados atualizados diretamente do Podio.
    """
    logger.info("AIESEC OGX | Iniciando processo de cadastro de novo lead...")

    return cadastrar_lead(body)


# ==============================
# Exportações do Módulo
# ==============================
__all__ = [
    "new_lead_ogx"
]