"""
Módulo de Auditoria e Controle de Tráfego.

Este middleware é executado após o processamento da rota (pós-request).
Sua função é dupla:
1. Registrar logs de acesso no padrão 'Common Log Format'.
2. Injetar cabeçalhos de controle de cache (HTTP Cache-Control) baseados no endpoint.
"""

# ==============================
# Importações (Dependencies)
# ==============================
import logging                      # Engine de logs nativa do Python
from pydantic import ConfigDict      # Validador de configurações para o decorador
from flask import request, Response # Objetos globais (Proxy) da requisição e resposta
from ..utils import agora_format_brasil_mes # Gerador de timestamp formatado

# ==============================
# Configurações e Instâncias Globais
# ==============================

# logger: Instanciado no escopo do módulo para otimizar performance (evita repetidas buscas na árvore de logs).
logger = logging.getLogger(__name__)

# NO_CACHE_ROUTES: Conjunto (set) de strings para busca exata.
# Utilizado para endpoints fixos. O acesso em 'set' tem complexidade O(1).
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

# NO_CACHE_PREFIXES: Tupla de prefixos para rotas dinâmicas ou diretórios.
# Necessário para capturar caminhos como /static/logo.png ou /openapi/swagger/index.html.
NO_CACHE_PREFIXES = (
    "/static/",
    "/openapi/swagger",
    "/apidoc/swagger",
    "/openapi/static/",
    "/openapi/redoc/",
    "/openapi/scalar/",
)

# ==============================
# Middleware de Auditoria
# ==============================

@validar(config=ConfigDict(arbitrary_types_allowed=True))
def register_url(response: Response) -> Response:
    """
    Intercepta a resposta para registrar log de auditoria e definir política de cache.

    Args:
        response (Response): O objeto de resposta retornado pela lógica da rota.

    Returns:
        Response: A resposta modificada com os cabeçalhos de cache injetados.
    """

    # --- 1. Extração de Metadados ---

    # protocol: Identifica a versão do HTTP (ex: HTTP/1.1); essencial para conformidade com o Common Log Format.
    protocol = request.environ.get("SERVER_PROTOCOL", "HTTP/1.1")

    # ip: Captura o endereço de rede do cliente ou do último proxy/load balancer.
    ip = request.remote_addr

    # hora: Carimbo de tempo customizado no formato dia/mês/ano hora:minuto:segundo.
    hora = agora_format_brasil_mes()

    # metodo: O verbo HTTP utilizado (GET, POST, PUT, DELETE, etc.).
    metodo = request.method

    # endpoint: O caminho absoluto da URL solicitada (sem parâmetros de query string).
    endpoint = request.path

    # --- 2. Registro de Auditoria ---

    # mensagem: Composição do log seguindo o padrão clássico de servidores Apache/Nginx.
    # Exemplo de saída: 192.168.1.1 - - [18/Fev/2026 13:40:00] "POST /api/v1/validarToken HTTP/1.1" 200 -
    mensagem = f'{ip} - - [{hora}] "{metodo} {endpoint} {protocol}" {response.status_code} -'
    logger.info(mensagem)

    # --- 3. Lógica de Injeção de Cache ---

    # Verifica se o endpoint atual está na lista negra de cache (exata ou por prefixo)
    if endpoint in NO_CACHE_ROUTES or endpoint.startswith(NO_CACHE_PREFIXES):
        # POLÍTICA: SEM CACHE (Segurança e Dados em Tempo Real)
        # 'no-store': Proíbe o armazenamento em disco.
        # 'no-cache, must-revalidate': Obriga a consulta ao servidor em cada acesso.
        # 'proxy-revalidate': Estende a obrigatoriedade para CDNs e Proxies intermediários.
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
        )

        # Pragma: Garante comportamento 'no-cache' em navegadores muito antigos (HTTP/1.0).
        response.headers["Pragma"] = "no-cache"

        # Expires: Data de expiração no passado (0) para invalidar o conteúdo imediatamente.
        response.headers["Expires"] = "0"
    else:
        # POLÍTICA: CACHE PADRÃO (Otimização de Performance)
        # 'public': Permite que o cache seja compartilhado (browser e proxies).
        # 'max-age=7200': O navegador guarda o recurso por 2 horas (7200 segundos).
        response.headers["Cache-Control"] = "public, max-age=7200, must-revalidate"

    return response

# ==============================
# Exportações do Módulo
# ==============================
__all__ = ['register_url']