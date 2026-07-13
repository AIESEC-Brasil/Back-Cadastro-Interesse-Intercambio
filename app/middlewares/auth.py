"""
Auth Middleware
---------------

Guardião de integridade e acesso. Este middleware atua como o 'Gatekeeper' da AIESEC,
validando se as requisições provêm de fontes autorizadas (API Keys) ou domínios confiáveis.

Regras de Governança:
- Bypass em rotas públicas (Whitelist).
- Verificação rigorosa de API Keys e IP de acesso (especialmente para documentação).
- Bloqueio de navegação direta em produção para proteger o endpoint.
"""

# ==============================
# Importações (Dependencies)
# ==============================

# Ferramentas de Sistema e Monitoramento
import logging                      # Sistema de registro para auditoria e monitoramento de eventos de segurança
import os                           # Interface com o Sistema Operacional (uso de variáveis de ambiente para IPs)
from typing import Literal

# Componentes do Framework Flask
from flask import Response          # Objeto de resposta HTTP do Flask para tipagem de retorno

from app.dto import HttpStatus
from ..dto import HttpStatus
from ..storage import storage

# Configurações de Segurança e Identidade (Core)
from ..config import (
    API_KEYS_PERMITIDAS             # Lista de chaves autorizadas para integração com parceiros
)
from ..core import (
    DOMINIOS_PERMITIDOS,            # Whitelist de URLs oficiais permitidas a consumir a API
    IS_PRODUCTION,                   # Flag de ambiente para ativação de travas de segurança em produção
    IS_TEST
)

# Utilitários Globais e Tipagem Estática
from typing import (
    List,                           # Tipagem para listas de strings
    Optional,                       # Tipagem para valores que podem ser nulos (como API Keys)
    Dict                            # Tipagem para estruturas de dicionário
)

from flask import (
    request,                        # Captura dados da requisição (Headers, Host, Path)
    jsonify,                        # Converte dicionários em respostas JSON padronizadas
)

# ==============================
# Configurações de Segurança
# ==============================

# Instância do Logger para rastreabilidade de tentativas de acesso
logger = logging.getLogger(__name__)

# ==============================
# Middleware de Validação
# ==============================

def verificar_origem() -> None | tuple[dict[str, str], Literal[HttpStatus.UNAUTHORIZED]] | tuple[Response, int]:
    """
    Middleware global de segurança.

    Analisa a autenticidade da origem através de camadas:
    1. Protocolo CORS (OPTIONS)
    2. Whitelist de rotas públicas
    3. Controle de acesso por IP (para /docs)
    4. Validação de API Key e Domínio de Host
    5. Proteção contra acesso direto via Navegador
    """

    ROTAS_PUBLICAS = {
        "/favicon.ico"
    }

    ROTAS_GRAFICAS = {
        "/api/docs",
        "/api/register"
    }

    if request.path in ROTAS_PUBLICAS:
        return None

    # 1. Bypass para 'Preflight' (CORS):
    # Permite que o navegador verifique as políticas do servidor sem bloqueio.
    if request.method == 'OPTIONS':
        return None

    logger.info("AIESEC Security | Iniciando autenticação de origem...")

    # ==========================
    # 2. Validação de IP (Acesso à Documentação)
    # ==========================
    # Verifica se o ambiente é de produção
    if IS_PRODUCTION or IS_TEST:
        # Restrição de segurança: Apenas IPs na lista branca podem ver a estrutura da API.
        # 1. Extração do caminho da URL (ex: /api/docs/...)
        path: str = request.path

        # 2. Segmentação do path para identificação do serviço
        parts: list[str] = path.strip("/").split("/")
        if parts[1] in ["docs"] or parts[0] in ["apidoc","openapi","static"]:
            allow_ip_list = storage.get_ip()
            if request.headers.get("X-Forwarded-For") not in allow_ip_list:
                logger.error("AIESEC Security | Bloqueio de IP: Tentativa não autorizada em /docs.")
                return {"erro": "Sua maquina não está autorizada a entrar nessa rota"},HttpStatus.UNAUTHORIZED
            return None

    # ==========================
    # 4. Validação de API Key
    # ==========================
    # Extrai a credencial enviada no Header 'X-API-KEY'.
    api_key: Optional[str] = request.headers.get("X-API-KEY")

    if api_key and api_key not in API_KEYS_PERMITIDAS:
        logger.error(f"AIESEC Security | Chave de Api {api_key} não autorizada.")
        return jsonify({"error": "API Key inválida"}), HttpStatus.UNAUTHORIZED

    # ==========================
    # 5. Validação de domínio (Host)
    # ==========================
    # Reconstrói a origem para comparação com os domínios permitidos (Whitelist).
    host: Optional[str] = f'{request.headers.get("Host")}'

    if host and host not in DOMINIOS_PERMITIDOS:
        if not api_key:
            # Caso o domínio seja externo e não haja chave de API, o acesso é negado.
            logger.error(f"AIESEC Security | Host não autorizado: {host}")
            return jsonify({"error": "Domínio não autorizado"}), HttpStatus.UNAUTHORIZED

    # ==========================
    # 6. Bloqueio de Acesso Direto (Navegador)
    # ==========================
    # Em produção, impede que a API seja consumida via navegação direta (URL no browser).
    if IS_PRODUCTION and request.headers.get("Sec-Fetch-Mode") == "navigate" and request.path not in ROTAS_GRAFICAS:
         logger.error("AIESEC Security | Bloqueio de requisição direta em Produção.")
         return jsonify({"error": "Bloqueado: requisições diretas não são permitidas"}), HttpStatus.UNAUTHORIZED

    logger.info("AIESEC Security | Origem autenticada com sucesso!")

    # Retorno None: Autoriza a continuidade do fluxo para o controller da rota.
    return None

# ==============================
# Exportações do Módulo
# ==============================
__all__ = [
    "verificar_origem"
]