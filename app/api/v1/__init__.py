"""Versão 1 da API - AIESEC Gateway.

Módulo de inicialização e agregação das rotas da versão 1 (v1).
Consolida e registra todos os sub-roteadores de entidades e paginações
(Escritórios, Universidades) sob o prefixo comum '/v1'.
"""

# ==============================================================================
# 1. IMPORTAÇÕES DA APLICAÇÃO E SUBMÓDULOS
# ==============================================================================

# Importação da classe Router do núcleo da aplicação
from app.router import Router

# Importação dos roteadores das entidades do pacote de paginação
from .paginacao import escritorios, universidades

# ==============================================================================
# 2. INICIALIZAÇÃO DO ROTEADOR V1
# ==============================================================================

# Instancia o roteador da V1 aplicando o prefixo de URL '/v1'
v1 = Router(name="v1", url_prefix="/v1")

# ==============================================================================
# 3. REGISTRO DOS SUBMÓDULOS DE ROTAS
# ==============================================================================

# Anexa as rotas e paginações de escritórios sob a árvore '/v1'
v1.register_api(escritorios)

# Anexa as rotas e paginações de universidades sob a árvore '/v1'
v1.register_api(universidades)


# ==============================================================================
# 4. EXPORTAÇÃO CONSOLIDADA E CONTRATO PÚBLICO
# ==============================================================================

# O __all__ limita a interface pública do pacote apenas à instância 'v1'
# configurada, encapsulando os submódulos de domínio.
__all__ = [
    "v1",  # Roteador consolidado contendo todas as rotas da versão 1
]