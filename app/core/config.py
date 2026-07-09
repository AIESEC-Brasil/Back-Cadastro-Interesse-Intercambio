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
)
import locale

# ==============================
# Identificação de Ambiente
# ==============================

# Flag booleana para identificar se a execução ocorre em ambiente de Produção
IS_PRODUCTION: bool = AMBIENTE in {"PRODUCTION", "PROD"}

# Flag booleana para identificar ambientes de não-produção (Desenvolvimento/Testes)
IS_NON_PROD: bool = AMBIENTE in {"DEVELOPMENT", "DEV", "TEST", "TESTING"}

# Validação de Segurança: Impede que a aplicação suba sem um ambiente definido
if not (IS_PRODUCTION or IS_NON_PROD):
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

# ==============================
# Exportações do Módulo
# ==============================

__all__ = [
    "DOMINIOS_PERMITIDOS", # Lista final de domínios para políticas de CORS
    "IS_PRODUCTION",       # Booleano para verificações de segurança/logs
    "IS_NON_PROD",          # Booleano para habilitar ferramentas de debug
    "configurar_idioma"
]