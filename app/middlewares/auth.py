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

# Componentes do Framework Flask
from flask import Response          # Objeto de resposta HTTP do Flask para tipagem de retorno

from ..dto import HttpStatus        # Enum com os Status Http
from ..storage import storage       # Armazenmaneto em Memorio de IP

# Configurações de Segurança e Identidade (Core)
from ..config import (
    API_KEYS_PERMITIDAS             # Lista de chaves autorizadas para integração com parceiros
)
from ..core import (
    DOMINIOS_PERMITIDOS,            # Whitelist de URLs oficiais permitidas a consumir a API
    IS_PRODUCTION,                  # Flag de ambiente para ativação de travas de segurança em produção
    IS_TEST                         # Flag de ambiente para ativação de travas de segurança em Teste
)

# Utilitários Globais e Tipagem Estática
from typing import (
    List,                           # Tipagem para listas de strings
    Optional,                       # Tipagem para valores que podem ser nulos (como API Keys)
    Dict,                           # Tipagem para estruturas de dicionário
    Literal                         # Tipagem para Literal
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
# Rotas
# ==============================
# Definição de listas de controle (usando sets para garantir performance de busca O(1))

# ROTAS_PUBLICAS: Recursos estáticos que não exigem validação de segurança.
# Evita processamento desnecessário para elementos de UI do navegador.
ROTAS_PUBLICAS = {"/favicon.ico"}

# ROTAS_GRAFICAS: Endpoints que renderizam interfaces HTML para o usuário.
# Exceções na trava de segurança de "Navegação Direta" para permitir acesso via browser.
ROTAS_GRAFICAS = {"/api/docs", "/api/register"}

# ROTAS_RESTRITAS_IP: Estruturas que expõem especificações técnicas da API.
# O acesso a estes diretórios é sensível e exige validação de IP em produção.
ROTAS_RESTRITAS_IP = ("/apidoc", "/openapi", "/static")

# ==============================
# Middleware de Validação
# ==============================

def verificar_origem() -> None | tuple[Dict[str, str], Literal[HttpStatus.UNAUTHORIZED]] | tuple[Response, int]:
    """
    Middleware global de governança e segurança (Gatekeeper).

    Intercepção de requisições HTTP para validar a integridade da origem antes
    do processamento pelos controllers. Implementa camadas de defesa em profundidade:

    Camadas de Validação:
        1. Bypass de Rotas Públicas: Ignora verificações para recursos essenciais (ex: /favicon.ico).
        2. Preflight Check: Bypass automático para requisições OPTIONS (CORS).
        3. Governança de Documentação: Verificação estrita de IP em ambiente de
            produção/teste para rotas sob '/docs', '/openapi' e '/static'.
        4. Autenticação de Integração: Validação de chave no header 'X-API-KEY'.
        5. Whitelist de Host: Bloqueio de tráfego vindo de domínios não homologados.
        6. Proteção contra Navegação: Bloqueio de acesso direto (browser navigation)
            em rotas de API para evitar exposição de dados em produção.

    Exemplos de Bloqueio:
        - GET /api/data (Navegador) -> Bloqueado (Security Error: Navigate Mode)
        - GET /openapi/swagger (IP não registrado) -> Bloqueado (401 Unauthorized)
        - POST /api/v1/update (Sem API Key ou Domínio inválido) -> Bloqueado (401 Unauthorized)

    Returns:
        None: Se a requisição for validada e autorizada.
        tuple: Objeto de erro (JSON) e status 401 se a validação falhar.
    """

    # 1. Bypass para rotas públicas e Preflight (CORS)
    # Se a requisição for um recurso básico (favicon) ou uma verificação de permissão CORS,
    # liberamos imediatamente para evitar latência no carregamento de recursos do navegador.
    if request.path in ROTAS_PUBLICAS or request.method == 'OPTIONS':
        return None

    # ==========================
    # 2. Validação de IP (Acesso à Documentação)
    # ==========================
    # Aplica bloqueio rigoroso apenas em ambientes de homologação ou produção.
    if IS_PRODUCTION or IS_TEST:
        if request.path.startswith(ROTAS_RESTRITAS_IP):
            # Acesso direto ao storage para garantir paralelismo total e leitura atualizada.
            # Cada thread/worker processa sua própria leitura de forma independente.
            allow_ip_list = set(storage.get_ip())
            if request.headers.get("X-Forwarded-For") not in allow_ip_list:
                logger.error("AIESEC Security | Bloqueio de IP: Tentativa não autorizada.")
                return {"erro": "Sua máquina não está autorizada a entrar nessa rota"}, HttpStatus.UNAUTHORIZED
            return None # IP validado, prossegue para o endpoint.

    # ==========================
    # 3. Validação de API Key
    # ==========================
    # Valida credenciais enviadas via cabeçalho para comunicações server-to-server.
    api_key: Optional[str] = request.headers.get("X-API-KEY")
    if api_key and api_key not in API_KEYS_PERMITIDAS:
        logger.error("AIESEC Security | Chave de API não autorizada.")
        return jsonify({"error": "API Key inválida"}), HttpStatus.UNAUTHORIZED

    # ==========================
    # 4. Validação de domínio (Host)
    # ==========================
    # Protege contra requisições maliciosas enviadas com cabeçalhos Host forjados.
    # Garante que a API só responda para os domínios homologados da AIESEC.
    host: Optional[str] = f'{request.headers.get("Host")}'
    if host and host not in DOMINIOS_PERMITIDOS:
        if not api_key: # Se não houver API Key, o domínio precisa estar na whitelist.
            logger.error(f"AIESEC Security | Host não autorizado: {host}")
            return jsonify({"error": "Domínio não autorizado"}), HttpStatus.UNAUTHORIZED

    # ==========================
    # 5. Bloqueio de Acesso Direto (Navegador)
    # ==========================
    # Em produção, navegadores enviam o cabeçalho 'Sec-Fetch-Mode: navigate'.
    # Isso bloqueia usuários comuns de digitarem URLs de APIs diretamente no browser,
    # reduzindo o risco de exposição de dados ou ataques de enumeração.
    if IS_PRODUCTION and request.headers.get("Sec-Fetch-Mode") == "navigate" and request.path not in ROTAS_GRAFICAS:
        logger.error("AIESEC Security | Bloqueio de requisição direta em Produção.")
        return jsonify({"error": "Bloqueado: requisições diretas não são permitidas"}), HttpStatus.UNAUTHORIZED

    # Se todas as verificações passarem, o fluxo retorna None e a requisição segue para o controller.
    return None

# ==============================
# Exportações do Módulo
# ==============================
__all__ = [
    "verificar_origem"
]