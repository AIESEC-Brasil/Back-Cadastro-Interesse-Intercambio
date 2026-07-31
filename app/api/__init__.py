"""Módulo de Agregação de Rotas da API - AIESEC Gateway.

Ponto central de inicialização do pacote 'api'. Importa o roteador base,
registra as versões das rotas (V1, etc.) e expõe a instância consolidada 'api'.
"""

# ==============================================================================
# 1. IMPORTAÇÕES DOS ROTEADORES E SUBMÓDULOS
# ==============================================================================

# Importa a instância 'api' que contém as configurações base e endpoints globais
from .api_doc import api

# Importa o sub-roteador contendo os endpoints da versão 1
from .v1 import v1


# ==============================================================================
# 2. REGISTRO E AGRECTAÇÃO DE ROTAS (BUILDER PATTERN)
# ==============================================================================

# Registra as rotas da Versão 1 no roteador principal da API
# Isso anexa os endpoints de '/v1' sob a árvore de rotas '/api'
api.register_api(v1)


# ==============================================================================
# 3. CONTRATO PÚBLICO E EXPORTAÇÃO
# ==============================================================================

# Limita a exposição do pacote apenas para o objeto 'api' já configurado,
# evitando a importação acidental de submódulos intermediários em app.py
__all__ = [
    "api",  # Roteador principal unificado contendo todas as versões conectadas
]