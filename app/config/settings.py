"""Módulo de Configurações Centrais (config.settings).

Responsável por carregar, validar e tipar todas as variáveis de ambiente.
Este módulo garante a imutabilidade de configuração e a segurança operacional
da aplicação, interrompendo a execução imediatamente em caso de ausência
de variáveis obrigatórias.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import os  # Acesso às variáveis de ambiente do Sistema Operacional
from typing import List  # Suporte para anotação de tipos de listas


# =================================================================
# 2. FUNÇÃO AUXILIAR DE VALIDAÇÃO
# =================================================================

def get_env_or_fail(var_name: str) -> str:
    """Recupera e valida uma variável de ambiente obrigatória do S.O.

    Args:
        var_name (str): Chave da variável de ambiente (ex: 'DB_CONNECT').

    Returns:
        str: Valor da variável limpo (sem espaços extras).

    Raises:
        ValueError: Interrompe o processo se a variável estiver ausente ou vazia.
    """
    valor = os.getenv(var_name, "").strip()
    if not valor:
        raise ValueError(
            f"CRITICAL ERROR: Variável de ambiente '{var_name}' não está definida!"
        )
    return valor


# =================================================================
# 3. CARREGAMENTO E TIPAGEM DE CONFIGURAÇÕES
# =================================================================

# Define o contexto de execução da aplicação: 'PRODUCTION', 'DEVELOPMENT' ou 'TEST'
AMBIENTE: str = get_env_or_fail("AMBIENTE").upper()

# Lista de chaves de API autorizadas a consumir os endpoints protegidos
API_KEYS_PERMITIDAS: List[str] = [
    k.strip() for k in get_env_or_fail("API_KEYS_PERMITIDAS").split(",")
]

# Domínios oficiais e autorizados para políticas de segurança e CORS
DOMINIOS_PERMITIDOS: List[str] = [
    d.strip() for d in get_env_or_fail("DOMINIOS_PERMITIDOS").split(",")
]

# String de conexão do ORM/SQLAlchemy (ex: postgresql://user:pass@host:5432/db)
DB_CONNECT: str = get_env_or_fail("DB_CONNECT")

# Identificador do script/Google Apps Script para integrações legadas
ID_APPSCRIPT_EXPA: str = get_env_or_fail("ID_APPSCRIPT_EXPA")

# Tempo de vida padrão para itens gravados em cache (em segundos)
CACHE_TTL: int = int(get_env_or_fail("CACHE_TTL"))

# Credenciais de autenticação na API do Podio
CLIENT_ID: str = get_env_or_fail("CLIENT_ID")
CLIENT_SECRET: str = get_env_or_fail("CLIENT_SECRET")
APP_ID: int = int(get_env_or_fail("APP_ID"))
APP_TOKEN: str = get_env_or_fail("APP_TOKEN")

# Token de autenticação da API global da AIESEC (EXPA / GIS)
TOKEN_EXPA: str = get_env_or_fail("TOKEN_EXPA")


# =================================================================
# 4. EXPORTAÇÃO PÚBLICA (INTERFACE DO MÓDULO)
# =================================================================

__all__ = [
    "AMBIENTE",  # Identificador do ambiente ativo (PROD, DEV, TEST)
    "DOMINIOS_PERMITIDOS",  # Lista de domínios permitidos para CORS e requisições
    "DB_CONNECT",  # URI de conexão com o banco de dados principal
    "API_KEYS_PERMITIDAS",  # Chaves de API autorizadas para autenticação
    "CACHE_TTL",  # Tempo de expiração (TTL) do cache em segundos
    "CLIENT_ID",  # ID do Cliente OAuth2 para o Podio
    "CLIENT_SECRET",  # Segredo do Cliente OAuth2 para o Podio
    "APP_ID",  # ID do aplicativo alvo no Podio
    "APP_TOKEN",  # Token do aplicativo alvo no Podio
    "TOKEN_EXPA",  # Token de autenticação da plataforma EXPA (GIS)
    "ID_APPSCRIPT_EXPA",  # ID de integração com Google Apps Script
]