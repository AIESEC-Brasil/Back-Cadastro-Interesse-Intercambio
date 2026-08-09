"""Módulo de Configurações Centrais (config.settings).

Responsável por carregar, validar, tipar e exportar todas as variáveis de
ambiente necessárias para a aplicação.

Este módulo garante a imutabilidade e segurança operacional do sistema ao:
1. Validar a presença de variáveis obrigatórias logo na inicialização.
2. Interromper a execução imediatamente (Fail-Fast) em caso de ausência de chaves.
3. Converter e tratar os tipos primitivos (int, bool, list) do arquivo .env.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import os  # Interface com o Sistema Operacional para leitura do ambiente
from typing import List, Optional  # Anotações de tipo para coleções e valores opcionais


# =================================================================
# 2. FUNÇÃO AUXILIAR DE VALIDAÇÃO E EXTRAÇÃO
# =================================================================

def get_env_or_fail(var_name: str, default: Optional[str] = None) -> str:
    """Recupera e valida uma variável de ambiente obrigatória ou retorna o valor padrão.

    Busca a chave informada no ambiente do S.O. e remove espaços em
    branco nas extremidades. Caso a variável esteja ausente ou vazia,
    retorna o valor 'default' se fornecido, ou dispara uma exceção.

    Args:
        var_name (str): Nome da chave de ambiente esperada (ex: 'DB_CONNECT').
        default (Optional[str]): Valor padrão opcional caso a variável não exista.

    Returns:
        str: Valor da variável higienizado ou o valor de fallback.

    Raises:
        ValueError: Lançado se a variável não estiver definida e sem valor padrão.
    """
    valor = os.getenv(var_name, "").strip()
    if not valor:
        if default is not None:
            return default
        raise ValueError(
            f"CRITICAL ERROR: Variável de ambiente '{var_name}' não está definida!"
        )
    return valor


# =================================================================
# 3. CARREGAMENTO, TRATAMENTO E TIPAGEM DE VARIÁVEIS
# =================================================================

# Contexto de execução do sistema (ex: 'PRODUCTION', 'DEVELOPMENT', 'TEST')
AMBIENTE: str = get_env_or_fail("AMBIENTE").upper()

# Chaves de API autorizadas a consumir endpoints protegidos (convertidas para lista)
API_KEYS_PERMITIDAS: List[str] = [
    k.strip() for k in get_env_or_fail("API_KEYS_PERMITIDAS").split(",")
]

# Domínios e origens oficiais permitidos para políticas de segurança e CORS
DOMINIOS_PERMITIDOS: List[str] = [
    d.strip() for d in get_env_or_fail("DOMINIOS_PERMITIDOS").split(",")
]

# Configurações do Banco de Dados (ORM / SQLAlchemy) com valor fallback local
DB_CONNECT: str = get_env_or_fail(
    "DB_CONNECT",
    "mysql+mysqlconnector://root:teste@172.19.135.162:3306/teste"
)

# Avalia se o pre-ping está ativo (compara de forma segura sem falhar em 'false')
DB_POOL_PRE_PING: bool = (
        get_env_or_fail("DB_POOL_PRE_PING").lower() in ("true", "1", "yes", "t")
)

# Tempo limite em segundos para reciclagem automática de conexões ociosas
DB_POOL_RECYCLE: int = int(get_env_or_fail("DB_POOL_RECYCLE"))

# Identificador de integração com Google Apps Script (sistemas legados)
APPSCRIPT_EXPA: str = get_env_or_fail("APPSCRIPT_EXPA")

# Tempo de vida padrão (TTL) em segundos para registros armazenados em cache
CACHE_TTL: int = int(get_env_or_fail("CACHE_TTL"))

# Credenciais de autenticação e acesso à API do Podio
CLIENT_ID: str = get_env_or_fail("CLIENT_ID")
CLIENT_SECRET: str = get_env_or_fail("CLIENT_SECRET")
APP_ID: int = int(get_env_or_fail("APP_ID"))
APP_TOKEN: str = get_env_or_fail("APP_TOKEN")

# Token de autenticação global para a plataforma EXPA (AIESEC GIS)
TOKEN_EXPA: str = get_env_or_fail("TOKEN_EXPA")


# =================================================================
# 4. EXPORTAÇÃO PÚBLICA (INTERFACE DO MÓDULO)
# =================================================================

__all__ = [
    "AMBIENTE",            # Contexto ativo da aplicação (PROD/DEV/TEST)
    "API_KEYS_PERMITIDAS",  # Chaves de API validadas para autenticação
    "DOMINIOS_PERMITIDOS",  # Lista de origens autorizadas para CORS
    "DB_CONNECT",          # String de conexão do SQLAlchemy
    "DB_POOL_PRE_PING",    # Validação de conexões antes de consultas
    "DB_POOL_RECYCLE",     # Intervalo de reciclagem de conexões em segundos
    "APPSCRIPT_EXPA",      # ID do script de integração Google Apps
    "CACHE_TTL",           # Tempo de expiração de itens em cache
    "CLIENT_ID",           # ID do cliente OAuth no Podio
    "CLIENT_SECRET",       # Segredo do cliente OAuth no Podio
    "APP_ID",              # ID do app no Podio
    "APP_TOKEN",           # Token do app no Podio
    "TOKEN_EXPA",          # Token do sistema EXPA/GIS
]