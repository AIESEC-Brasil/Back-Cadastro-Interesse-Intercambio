"""
API Router - AIESEC Security Gateway.

Módulo responsável pela agregação central das rotas da API.
Aplica versionamento, controle de acesso via Whitelist de IP e fornece
interfaces dinâmicas de documentação técnica (OpenAPI/Swagger/Scalar).
"""

# ==============================================================================
# 1. IMPORTAÇÕES DA BIBLIOTECA PADRÃO E TERCEIROS
# ==============================================================================

# O módulo 'os' permite a interação com variáveis de ambiente do sistema operacional
import os
from typing import Any

# Importações do framework Flask para renderização de templates e gerenciamento de requisições
from flask import redirect, render_template, request
from werkzeug.wrappers import Response
from flask_openapi3 import Tag

# ==============================================================================
# 2. IMPORTAÇÕES DE MÓDULOS INTERNOS DA APLICAÇÃO
# ==============================================================================

# DTO interno que encapsula códigos de status HTTP padrão
from ..dto import BaseErrorResponse, HttpStatus

# Decorator de segurança que intercepta requisições e valida o IP do cliente
from ..middlewares import require_ip_whitelist

# Instância personalizada do roteador para agregação de endpoints
from ..router import Router

# Instância do gerenciador de armazenamento de IPs permitidos em memória/persistência
from ..storage import storage

# ==============================================================================
# 3. CONFIGURAÇÃO DO ROTEADOR DA API
# ==============================================================================

# Instancia o roteador principal configurando o prefixo global de URL '/api'
api: Router = Router(name="api", url_prefix="/api")


# ==============================================================================
# 4. DEFINIÇÃO DAS ROTAS E ENDPOINTS
# ==============================================================================

# ===============================================================================
# DOCUMENTAÇÃO DA ROTA DE DOCUMENTAÇÃO
# ===============================================================================
DOCUMENTACAO_DESCRIPTION: str = """\
Apresenta links para as especificações OpenAPI e interfaces de documentação
interativa. Requer IP autorizado fora do ambiente DEV."""

DOCUMENTACAO_RESPONSES: dict[int | str, Any] = {
    200: {
        "description": "Página HTML com os links da documentação.",
        "content": {"text/html": {"schema": {"type": "string"}}},
    },
    401: {
        "description": "IP cliente não autorizado.",
        "content": {"text/html": {"schema": {"type": "string"}}},
    },
    422: BaseErrorResponse,
}


# ===============================================================================
# ROTA DA PÁGINA DE DOCUMENTAÇÃO
# ===============================================================================
@api.get(
    "/docs",
    summary="Exibir a documentação da API",
    tags=[Tag(name="Documentação")],
    description=DOCUMENTACAO_DESCRIPTION,
    responses=DOCUMENTACAO_RESPONSES,
)
@require_ip_whitelist
def documentacao() -> str:
    """Renderiza o portal de documentação da rota `/api/docs`."""
    # Mapeamento categorizado das rotas de documentação técnica expostas pelo Gateway
    rotas: dict[str, list[str]] = {
        "Swagger & OAuth": [
            "/openapi/swagger",
            "/openapi/swagger/<path:filename>",
            "/openapi/oauth2-redirect.html",
        ],
        "Scalar, Redoc & Elements": [
            "/openapi/scalar",
            "/openapi/redoc",
            "/openapi/elements",
            "/openapi/elements/<path:filename>",
            "/openapi/redoc/<path:filename>",
            "/openapi/scalar/<path:filename>",
        ],
        "RapiDoc & RapiPDF": [
            "/openapi/rapidoc",
            "/openapi/rapidoc/<path:filename>",
            "/openapi/rapipdf",
            "/openapi/rapipdf/<path:filename>",
        ],
        "Especificações (JSON/GERAL)": [
            "/openapi/openapi.json",
            "/openapi",  # Rota raiz da especificação
        ],
        "Arquivos Estáticos & Assets": [
            "/static/<path:filename>",
            "/openapi/static/<path:filename>",
        ],
    }

    # Renderiza o template HTML externo com os links categorizados.
    return render_template("docs.html", rotas=rotas)


# ===============================================================================
# DOCUMENTAÇÃO DA ROTA DE AUTORIZAÇÃO DE IP
# ===============================================================================
REGISTRO_DESCRIPTION: str = """\
Registra na whitelist o IP informado em `X-Forwarded-For` ou, se ausente, o
endereço remoto da conexão. Em seguida redireciona para `/api/docs`. Não recebe
parâmetros nem corpo."""

REGISTRO_RESPONSES: dict[int | str, Any] = {
    308: {
        "description": "Redirecionamento permanente para `/api/docs`.",
        "headers": {
            "Location": {
                "description": "URL de destino do redirecionamento.",
                "schema": {"type": "string"},
            }
        },
    },
    422: BaseErrorResponse,
}


# ===============================================================================
# ROTA DE AUTORIZAÇÃO DE IP
# ===============================================================================
@api.get(
    "/register",
    summary="Autorizar IP e abrir a documentação",
    tags=[Tag(name="Documentação")],
    description=REGISTRO_DESCRIPTION,
    responses=REGISTRO_RESPONSES,
)
def registro() -> tuple[Response, int]:
    """Autoriza o IP cliente e redireciona na rota `/api/register`."""
    # Extrai o IP considerando proxies/load balancers ou pega o IP direto do cliente
    client_ip: str = (
        request.headers.get("X-Forwarded-For") or request.remote_addr or ""
    )

    # Registra o IP capturado no banco/memória de autorização
    storage.add_ip(client_ip)

    # Redireciona o usuário de forma permanente para o portal de documentação
    return redirect("/api/docs"), int(HttpStatus.PERMANENT_REDIRECT)


# ==============================================================================
# 5. EXPORTAÇÕES DO MÓDULO
# ==============================================================================

# Expõe explicitamente o objeto de rotas da API para inclusão no App principal
__all__ = [
    "api",  # Instância Router com as rotas /docs e /register anexadas
]
