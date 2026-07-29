"""
Configuração derivada por ambiente (produção vs não-produção).

Define domínios permitidos (CORS/origem), URLs de conexão e flags de ambiente,
com base em constantes importadas de app.config.settings.
"""

# ==============================
# Importações de Configurações
# ==============================
# Importa as constantes brutas do arquivo de configurações central (settings.py)
from ..config import (
    AMBIENTE,           # String identificadora do ambiente (ex: 'PROD', 'DEV')
    DOMINIOS_PERMITIDOS,  # Lista de domínios oficiais da organização
    DB_CONNECT
)
from ..clients import metadados  # Função cliente para buscar campos e configurações do Podio
from ..clients import getAcessToken # Client responsável pelo handshake de OAuth2 com a API do Podio
from ..cache import cache           # Mecanismo de persistência temporária para otimizar performance
from ..config import CLIENT_SECRET, CLIENT_ID, APP_ID, APP_TOKEN
import locale

# ==============================
# Identificação de Ambiente
# ==============================

# Flag booleana para identificar se a execução ocorre em ambiente de Produção
IS_PRODUCTION: bool = AMBIENTE in {"PRODUCTION", "PROD"}

# Flag booleana para identificar ambientes de não-produção (Desenvolvimento/Testes)
IS_DEV: bool = AMBIENTE in {"DEVELOPMENT", "DEV"}
IS_TEST: bool = AMBIENTE in {"TEST", "TESTING"}

# Validação de Segurança: Impede que a aplicação suba sem um ambiente definido
if not (IS_PRODUCTION or IS_DEV or IS_TEST):
    raise ValueError(f"Ambiente inválido detectado: {AMBIENTE}")

# ==============================
# Definição de Variáveis Dinâmicas
# ==============================


def configurar_idioma():
    # Lista de nomes comuns para o mesmo idioma
    locales_tentativa = ["pt_BR.UTF-8", "pt_BR.utf8", "pt_BR", "Portuguese_Brazil.1252"]

    for loc in locales_tentativa:
        try:
            locale.setlocale(locale.LC_TIME, loc)
            print(f"Sucesso! Locale definido para: {loc}")
            return True
        except locale.Error:
            continue

    return False

async def pre_carregamento_metadados() -> None:
    """Pré-carrega os tokens de autenticação e metadados das aplicações do Podio no cache.

    A função estrutura as credenciais necessárias para cada integração e executa
    o carregamento assíncrono do token de acesso do Podio e dos metadados dos
    formulários/cards correspondentes.

    Raises:
        NameError: Se as credenciais globais (CLIENT_SECRET, CLIENT_ID, etc.) não
            estiverem definidas no escopo.
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
        fetch=lambda: getAcessToken(ogx_config["credenciais"]),  # Use async lambda/def se getAcessToken for async
        baixando="Chave de Acesso ao Podio ('new-lead-ogx')",
    )

    # Busca no cache ou recupera/armazena os metadados dos campos do aplicativo Podio
    await cache.get_or_set(
        key="metadados_card-ogx",
        fetch=lambda: metadados(
            chave=ogx_config["key"],
            APP_ID=APP_ID,
        ),
        baixando="Metadados de Novos lead B2C",
    )
# ==============================
# Exportações do Módulo
# ==============================

__all__ = [

    "AMBIENTE",
    "DOMINIOS_PERMITIDOS", # Lista final de domínios para políticas de CORS
    "IS_PRODUCTION",       # Booleano para verificações de segurança/logs
    "IS_DEV",          # Booleano para habilitar ferramentas de debug
    "IS_TEST",
    "DB_CONNECT",
    "configurar_idioma",
    "pre_carregamento_metadados"
]