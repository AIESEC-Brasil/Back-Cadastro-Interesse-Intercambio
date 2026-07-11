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
from .router import Router  # Classe base de roteamento integrada ao OpenAPI3
from app.cache import cache  # Gerenciador de cache para otimizar chamadas de API
from app.config import APP_ID  # ID do App de Leads B2C no Podio (configurado no .env)
from app.clients import metadados  # Função cliente para buscar campos e configurações do Podio
from app.dto import Metadados # DTO para validação e serialização de metadados do Podio
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

@new_lead_ogx.get("/metadados",responses={200:Metadados})
def buscar_metadados() -> Metadados:
    """
    Retorna a estrutura de campos do App de Leads B2C do Podio.

    Lógica de Cache:
    - Chave: 'metadados_card-ogx'
    - Autenticação: Utiliza o token específico de OGX ('ogx-token-podio')
    - Expiração: Segue o CACHE_TTL global.
    """
    # A função get_or_set do cache gerencia a lógica de expiração e armazenamento.
    response,status = cache.get_or_set(
        key="metadados_card-ogx",
        fetch=lambda: metadados(
            chave="ogx-token-podio",  # Busca o token de intercâmbio no cache/auth
            APP_ID=APP_ID  # Aponta para o App de B2C
        ),
        baixando="Metadados de Novos lead B2C"
    )
    # Ajusta o cabeçalho de Content-Type para JSON, garantindo compatibilidade com clientes REST.
    response.headers["Content-Type"] = "application/json"
    
    # Retorna o conteúdo armazenado no dicionário do cache
    return Metadados(**cache.store["metadados_card-ogx"]).model_dump()


@new_lead_ogx.post("/cadastro")
def criar_incricao():
    """
    Endpoint para recepção de novos leads de intercâmbio.
    (Em desenvolvimento: integrará com o controller de cadastro OGX).
    """
    return "<H1>ROTA PARA CADASTRO DE LEADS<H1>"


# ==============================
# Exportações do Módulo
# ==============================
__all__ = [
    "new_lead_ogx"
]