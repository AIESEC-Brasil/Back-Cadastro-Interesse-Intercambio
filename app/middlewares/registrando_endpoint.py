"""Módulo de Auditoria e Controle de Tráfego.

Este middleware é executado após o processamento da rota (pós-request).
Sua função é dupla:
1. Registrar logs de acesso no padrão 'Common Log Format'.
2. Injetar cabeçalhos de controle de cache (HTTP Cache-Control) baseados no endpoint.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import logging  # Engine de logs nativa do Python

from flask import Response, request  # Objetos globais de requisição e resposta do Flask
from pydantic import ConfigDict  # Validador de configurações para o decorador

from ..utils import agora_format_brasil_mes  # Gerador de timestamp formatado

# =================================================================
# 2. CONFIGURAÇÕES E INSTÂNCIAS GLOBAIS
# =================================================================

# Instanciado no escopo do módulo para otimizar busca na árvore de logs
logger = logging.getLogger(__name__)

# Conjunto (set) de strings para busca exata de rotas sem cache (Complexidade O(1))
NO_CACHE_ROUTES = {
    "/api/docs",
    "/openapi",
    "/openapi/scalar",
    "/openapi/redoc",
    "/openapi/elements",
    "/openapi/rapidoc",
    "/openapi/rapipdf",
    "/openapi/openapi.json",
    "/apidoc/openapi.json",
}

# Tupla de prefixos para checagem em rotas dinâmicas ou diretórios
NO_CACHE_PREFIXES = (
    "/static/",
    "/openapi/swagger",
    "/apidoc/swagger",
    "/openapi/static/",
    "/openapi/redoc/",
    "/openapi/scalar/",
)


# =================================================================
# 3. MIDDLEWARE DE AUDITORIA E TRÁFEGO
# =================================================================

@validar(config=ConfigDict(arbitrary_types_allowed=True))
def register_url(response: Response) -> Response:
    """Intercepta a resposta para registrar log de auditoria e definir política de cache.

    Args:
        response (Response): O objeto de resposta retornado pela lógica da rota.

    Returns:
        Response: A resposta modificada com os cabeçalhos de cache injetados.
    """
    # --- 1. Extração de Metadados da Requisição ---

    # Identifica a versão do protocolo HTTP
    protocol = request.environ.get("SERVER_PROTOCOL", "HTTP/1.1")

    # Captura o IP do cliente ou do proxy/load balancer
    ip = request.remote_addr

    # Carimbo de tempo formatado no padrão nacional
    hora = agora_format_brasil_mes()

    # Verbo HTTP (GET, POST, PUT, DELETE, etc.)
    metodo = request.method

    # Caminho absoluto da URL solicitada
    endpoint = request.path

    # --- 2. Registro de Log de Auditoria ---

    # Mensagem no formato clássico Common Log Format (Apache/Nginx)
    mensagem = (
        f'{ip} - - [{hora}] "{metodo} {endpoint} {protocol}" '
        f"{response.status_code} -"
    )
    logger.info(mensagem)

    # --- 3. Lógica de Injeção de Cabeçalhos de Cache ---

    # Verifica se o endpoint atual requer neutralização de cache
    if endpoint in NO_CACHE_ROUTES or endpoint.startswith(NO_CACHE_PREFIXES):
        # Política de segurança e tempo real (Sem Cache)
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
        )

        # Suporte a navegadores antigos (HTTP/1.0)
        response.headers["Pragma"] = "no-cache"

        # Expira o recurso imediatamente no navegador
        response.headers["Expires"] = "0"
    else:
        # Política de Otimização de Desempenho (Cache Padrão de 2 horas)
        response.headers["Cache-Control"] = (
            "public, max-age=7200, must-revalidate"
        )

    return response


# =================================================================
# 4. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["register_url"]