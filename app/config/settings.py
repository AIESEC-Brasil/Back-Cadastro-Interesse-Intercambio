"""
config.settings
---------------

Configuração central da aplicação.
Responsável por carregar, validar e tipar variáveis de ambiente.

Este módulo segue o princípio de imutabilidade de configuração e
garante a segurança operacional do sistema.
"""

# ==============================
# Importações (Dependencies)
# ==============================
# Importamos do nosso pacote 'globals.std' para manter a consistência de tipos e módulos
import os
from typing import List

# ================================
# FUNÇÃO AUXILIAR DE VALIDAÇÃO
# ================================

def get_env_or_fail(var_name: str) -> str:
    """
    Recupera uma variável de ambiente obrigatória do S.O.

    Args:
        var_name (str): Nome da chave (ex: 'DB_PRODUCAO').

    Returns:
        str: Valor limpo (sem espaços em branco).

    Raises:
        ValueError: Interrompe a execução se a variável estiver ausente ou vazia.
    """
    valor = os.getenv(var_name, "").strip()
    if not valor:
        raise ValueError(f"CRITICAL ERROR: Variável de ambiente '{var_name}' não está definida!")
    return valor


# ================================
# AMBIENTE E SEGURANÇA
# ================================

# Define o contexto de execução: 'PRODUCTION', 'DEVELOPMENT' ou 'TEST'
AMBIENTE: str = get_env_or_fail("AMBIENTE").upper()

# Lista de chaves de API autorizadas para consumir os endpoints protegidos
API_KEYS_PERMITIDAS: List[str] = [
    k.strip() for k in get_env_or_fail("API_KEYS_PERMITIDAS").split(",")
]

# ================================
# POLÍTICAS DE DOMÍNIO (CORS)
# ================================
# Domínios oficiais da AIESEC para produção
DOMINIOS_PERMITIDOS: List[str] = get_env_or_fail("DOMINIOS_PERMITIDOS").split(",")


# ================================
# INTEGRAÇÕES GOOGLE APPS SCRIPT
# ================================
# Endpoints legados ou utilitários para busca e inserção via Google Sheets/Email
ID_APPSCRIPT_EXPA = get_env_or_fail("ID_APPSCRIPT_EXPA")

# ================================
# ACESSO EXTERNO E PERFORMANCE
# ================================

# Tempo de vida do cache em segundos (ex: 3600 para 1 hora)
CACHE_TTL: int = int(get_env_or_fail("CACHE_TTL"))


# ================================
# CREDENCIAIS PODIO - Novos Leads B2C(OGX) E PROCESSO SELETIVO(PSEL)
# ================================
# Configurações de API para os diferentes Workspaces da AIESEC no Podio
CLIENT_ID = get_env_or_fail("CLIENT_ID")
CLIENT_SECRET = get_env_or_fail("CLIENT_SECRET")
APP_ID = get_env_or_fail("APP_ID")
APP_TOKEN= get_env_or_fail("APP_TOKEN")

# ================================
# INTEGRAÇÃO GLOBAL (EXPA)
# ================================
# Token de acesso à API oficial da AIESEC International (GIS)
TOKEN_EXPA = get_env_or_fail("TOKEN_EXPA")

# ================================
# EXPORTAÇÃO PÚBLICA (INTERFACE)
# ================================



__all__ = [
    "AMBIENTE",
    "DOMINIOS_PERMITIDOS",
    "API_KEYS_PERMITIDAS",
    "CACHE_TTL",
    "CLIENT_ID",
    "CLIENT_SECRET",
    "APP_ID",
    "APP_TOKEN",
    "TOKEN_EXPA",
    "ID_APPSCRIPT_EXPA",
]