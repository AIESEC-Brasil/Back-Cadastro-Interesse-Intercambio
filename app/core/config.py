"""Configuração derivada por ambiente (produção vs não-produção).

Define domínios permitidos (CORS/origem), URLs de conexão e flags de ambiente,
com base em constantes importadas de app.config.settings.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import locale  # Manipulação de configurações regionais e de idioma
from typing import Any, Dict  # Suporte para anotações de tipagem estática
from ..repository import (  # Métodos de consulta ao banco de dados/repositório
    buscar_todas_universidades,
    buscar_todos_cl,
)
from ..cache import cache  # Mecanismo de persistência temporária/cache
from ..clients import get_access_token  # Client para handshake de OAuth2
from ..clients import metadados  # Client para metadados de campos do Podio
from ..config import (  # Constantes brutas importadas da configuração central
    AMBIENTE,
    APP_ID,
    APP_TOKEN,
    CLIENT_ID,
    CLIENT_SECRET,
    DB_CONNECT,
    DOMINIOS_PERMITIDOS,
)

# =================================================================
# 2. IDENTIFICAÇÃO DE AMBIENTE E FLAGS
# =================================================================

# Flag booleana para identificar se a execução ocorre em ambiente de Produção
IS_PRODUCTION: bool = AMBIENTE in {"PRODUCTION", "PROD"}

# Flags booleanas para identificar ambientes de Desenvolvimento e Testes
IS_DEV: bool = AMBIENTE in {"DEVELOPMENT", "DEV"}
IS_TEST: bool = AMBIENTE in {"TEST", "TESTING"}

# Validação de Segurança: Impede que a aplicação suba sem ambiente válido
if not (IS_PRODUCTION or IS_DEV or IS_TEST):
    raise ValueError(f"Ambiente inválido detectado: {AMBIENTE}")


# =================================================================
# 3. FUNÇÕES E CONFIGURAÇÕES DINÂMICAS
# =================================================================

def configurar_idioma() -> bool:
    """Tenta definir o locale da aplicação para o idioma Português (Brasil).

    Returns:
        bool: True se algum locale compatível for configurado com sucesso,
            False caso contrário.
    """
    # Lista de nomes e codificações comuns para o locale PT-BR
    locales_tentativa = [
        "pt_BR.UTF-8",
        "pt_BR.utf8",
        "pt_BR",
        "Portuguese_Brazil.1252",
    ]

    for loc in locales_tentativa:
        try:
            locale.setlocale(locale.LC_TIME, loc)
            return True
        except locale.Error:
            continue

    return False


async def pre_carregamento_metadados() -> None:
    """Pré-carrega tokens de autenticação e metadados de apps no cache.

    Estrutura as credenciais para cada integração e executa o carregamento
    assíncrono do token de acesso do Podio e dos metadados das aplicações.
    """
    # Mapeamento de configurações e credenciais por fluxo/integração
    config_map: Dict[str, Dict[str, Any]] = {
        "new-lead-ogx": {
            "key": "ogx-token-podio",
            "credenciais": {
                "CLIENT_SECRET": CLIENT_SECRET,
                "CLIENT_ID": CLIENT_ID,
                "APP_ID": APP_ID,
                "APP_TOKEN": APP_TOKEN,
            },
        }
    }

    # Seleciona a configuração específica do fluxo OGX
    ogx_config: Dict[str, Any] = config_map["new-lead-ogx"]

    # Busca no cache ou gera/armazena o token de acesso do Podio
    await cache.get_or_set(
        key=ogx_config["key"],
        fetch=lambda: get_access_token(ogx_config["credenciais"]),
        baixando="Chave de Acesso ao Podio ('new-lead-ogx')",
    )

    # Busca no cache ou recupera/armazena os metadados do aplicativo Podio
    await cache.get_or_set(
        key="metadados_card-ogx",
        fetch=lambda: metadados(
            chave=ogx_config["key"],
            app_id=APP_ID,
        ),
        baixando="Metadados de Novos lead B2C",
    )

    await cache.get_or_set(
        key="divisao-mercado-escritorios",
        fetch=lambda: buscar_todos_cl(),
        baixando="Metadados da divisão de mercado por escritorio",
    )

    await cache.get_or_set(
    key="divisao-mercado-universidades",
    fetch=lambda: buscar_todas_universidades(),
    baixando="Metadados da divisão de mercado por Universidades",
)


# =================================================================
# 4. EXPORTAÇÕES DO MÓDULO
# =================================================================
__all__ = [
    "AMBIENTE",  # Nome/identificador bruto do ambiente (PROD, DEV, TEST)
    "DOMINIOS_PERMITIDOS",  # Whitelist de URLs/origens para segurança de CORS e Host
    "IS_PRODUCTION",  # Booleano que indica se o ambiente é de Produção
    "IS_DEV",  # Booleano que indica se o ambiente é de Desenvolvimento
    "IS_TEST",  # Booleano que indica se o ambiente é de Teste/Homologação
    "DB_CONNECT",  # String de conexão/URI com o banco de dados
    "configurar_idioma",  # Função utilitária para definir locale da aplicação para PT-BR
    "pre_carregamento_metadados",  # Rotina assíncrona para aquecimento e cache de dados do Podio
]