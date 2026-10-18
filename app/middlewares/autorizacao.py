"""Auth Middleware.

Guardião de integridade e acesso. Este middleware atua como o 'Gatekeeper' da AIESEC,
validando se as requisições provêm de fontes autorizadas (API Keys) ou domínios confiáveis.

Regras de Governança:
- Bypass em rotas públicas (Whitelist).
- Verificação rigorosa de API Keys e IP de acesso (especialmente para documentação).
- Bloqueio de navegação direta em produção para proteger os endpoints.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================

# Ferramentas de Sistema e Monitoramento
import logging  # Sistema de registro para auditoria e monitoramento de eventos de segurança
import os  # Interface com o Sistema Operacional

# Utilitários Globais e Tipagem Estática
from typing import Dict, List, Literal, Optional, Tuple, Union

# Componentes do Framework Flask
from flask import Response, jsonify, request

# Configurações de Segurança e Identidade (Core)
from ..config import (
    API_KEYS_PERMITIDAS,  # Lista de chaves autorizadas para integração com parceiros
)
from ..core import (
    DOMINIOS_PERMITIDOS,  # Whitelist de URLs oficiais permitidas a consumir a API
    IS_PRODUCTION,  # Flag de ambiente para ativação de travas de segurança em produção
    IS_TEST,  # Flag de ambiente para ativação de travas de segurança em Teste
)
from ..dto import HttpStatus  # Enum ou estrutura com os Status HTTP
from ..storage import storage  # Armazenamento em memória de IP

# =================================================================
# 2. CONFIGURAÇÕES E CONSTANTES DE SEGURANÇA
# =================================================================

# Instância do Logger para rastreabilidade de tentativas de acesso
logger: logging.Logger = logging.getLogger(__name__)

# ROTAS_PUBLICAS: Recursos estáticos que não exigem validação de segurança.
ROTAS_PUBLICAS: set[str] = {"/favicon.ico"}

# ROTAS_GRAFICAS: Endpoints que renderizam interfaces HTML para o usuário.
ROTAS_GRAFICAS: set[str] = {"/api/docs", "/api/register"}

# ROTAS_RESTRITAS_IP: Estruturas que expõem especificações técnicas da API.
ROTAS_RESTRITAS_IP: tuple[str, ...] = ("/apidoc", "/openapi", "/static")


def _registrar_bloqueio(motivo: str) -> None:
    """Registra tentativas barradas com status e dados básicos da requisição."""
    forwarded_for: str = request.headers.get("X-Forwarded-For", "")
    client_ip: str = (
        forwarded_for.split(",", 1)[0].strip() or request.remote_addr or "-"
    )
    logger.warning(
        "AIESEC Security | acesso não autorizado | HTTP %s %s | motivo=%s | "
        "método=%s | endpoint=%s | IP cliente=%s",
        HttpStatus.UNAUTHORIZED.value,
        HttpStatus.UNAUTHORIZED.name,
        motivo,
        request.method,
        request.path,
        client_ip,
    )


# =================================================================
# 3. MIDDLEWARE DE VALIDAÇÃO DE ORIGEM
# =================================================================

def verificar_origem() -> Union[None, Tuple[Response, int]]:
    """Middleware global de governança e segurança (Gatekeeper).

    Intercepta requisições HTTP para validar a integridade da origem antes
    do processamento pelos controllers. Implementa camadas de defesa em profundidade:

    Camadas de Validação:
        1. Bypass de Rotas Públicas: Ignora verificações para recursos essenciais (ex: /favicon.ico).
        2. Preflight Check: Bypass automático para requisições OPTIONS (CORS).
        3. Governança de Documentação: Verificação estrita de IP em ambiente de
           produção/teste para rotas sob '/apidoc', '/openapi' e '/static'.
        4. Autenticação de Integração: Validação de chave no header 'X-API-KEY'.
        5. Whitelist de Host: Bloqueio de tráfego vindo de domínios não homologados.
        6. Proteção contra Navegação: Bloqueio de acesso direto (browser navigation)
           em rotas de API para evitar exposição de dados em produção.

    Returns:
        Union[None, Tuple[Response, int]]:
            Retorna None se a requisição for validada com sucesso, ou uma tupla com
            Response e código HTTP 401 caso a validação falhe.
    """

    # 1. Bypass para rotas públicas e Preflight (CORS)
    if request.path in ROTAS_PUBLICAS or request.method == "OPTIONS":
        return None

    # =================================================================
    # 2. Validação de IP (Acesso à Documentação em Produção / Teste)
    # =================================================================
    if IS_PRODUCTION or IS_TEST:
        if request.path.startswith(ROTAS_RESTRITAS_IP):
            # Carrega a lista de IPs permitidos armazenada no storage
            allow_ip_list: set[str] = set(storage.get_ip())

            # Extrai o IP considerando proxies/load balancers intermediários
            raw_ip: str | None = request.headers.get(
                "X-Forwarded-For", request.remote_addr
            )
            client_ip: str = raw_ip.split(",")[0].strip() if raw_ip else ""

            if client_ip not in allow_ip_list:
                _registrar_bloqueio("IP fora da lista autorizada")
                mensagem_erro: dict[str, str] = {
                    "erro": "Sua máquina não está autorizada a entrar nessa rota"
                }
                return jsonify(mensagem_erro), HttpStatus.UNAUTHORIZED

            return None  # IP validado, prossegue para o endpoint.

    # =================================================================
    # 3. Validação de API Key (Server-to-Server)
    # =================================================================
    api_key: Optional[str] = request.headers.get("X-API-KEY")
    if api_key and api_key not in API_KEYS_PERMITIDAS:
        _registrar_bloqueio("chave de API inválida")
        return jsonify({"error": "API Key inválida"}), HttpStatus.UNAUTHORIZED

    # =================================================================
    # 4. Validação de Domínio (Host Header)
    # =================================================================
    host: Optional[str] = request.headers.get("Host")
    if host and host not in DOMINIOS_PERMITIDOS:
        if not api_key:  # Se não houver API Key, o domínio precisa estar na whitelist
            _registrar_bloqueio(f"host não autorizado: {host}")
            return (
                jsonify({"error": "Domínio não autorizado"}),
                HttpStatus.UNAUTHORIZED,
            )

    # =================================================================
    # 5. Bloqueio de Acesso Direto via Navegador em Produção
    # =================================================================
    if (
            IS_PRODUCTION
            and request.headers.get("Sec-Fetch-Mode") == "navigate"
            and request.path not in ROTAS_GRAFICAS
    ):
        _registrar_bloqueio("navegação direta bloqueada em produção")
        return (
            jsonify({"error": "Bloqueado: requisições diretas não são permitidas"}),
            HttpStatus.UNAUTHORIZED,
        )

    # Se todas as verificações passarem, libera a execução para o controller
    return None


# =================================================================
# 4. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["verificar_origem"]
