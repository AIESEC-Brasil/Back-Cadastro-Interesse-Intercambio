"""
Módulo de Infraestrutura: AIESEC Security - Podio Auth Middleware.

Garante que cada conexão com o Podio seja autenticada e otimizada via cache.
Atua como um guardião, assegurando que o serviço correto acesse os dados
necessários com as credenciais OAuth2 adequadas.

Para garantir compatibilidade com rotas síncronas e evitar problemas de validação
no Flask-OpenAPI3, este middleware resolve as chamadas assíncronas do gerenciador de
cache de forma síncrona segura utilizando a ponte `async_to_sync`.
"""

# =================================================================
# IMPORTAÇÕES (DEPENDENCIES)
# =================================================================

# Ferramentas de Sistema e Logs
import logging                      # Registro de eventos para monitoramento e auditoria de erros
from functools import wraps         # Garante a preservação dos metadados da função original decorada

# Conversor de contexto Assíncrono para Síncrono
from asgiref.sync import async_to_sync

# Componentes do Framework Flask
from flask import request           # Extensão do objeto request para capturar headers e caminhos

# Recursos Internos da Aplicação
from ..clients import getAcessToken # Client responsável pelo handshake de OAuth2 com a API do Podio
from ..cache import cache           # Mecanismo de persistência temporária para otimizar performance

# Utilitários de Tipagem Estática
from typing import Any, Dict, Callable

# Configurações de Segurança e Identidade (Secrets)
from ..config import CLIENT_SECRET, CLIENT_ID, APP_ID, APP_TOKEN


# =================================================================
# CONFIGURAÇÃO DE SERVIÇOS (CONFIG_MAP)
# =================================================================

# Mapa de Atribuição: Associa o identificador do serviço às credenciais específicas.
# "Leadership is about making others better as a result of your presence."
CONFIG_MAP = {
    "new-lead-ogx": {
        "key": "ogx-token-podio",
        "credenciais": {
            "CLIENT_SECRET": CLIENT_SECRET,
            "CLIENT_ID": CLIENT_ID,
            "APP_ID": APP_ID,
            "APP_TOKEN": APP_TOKEN
        }
    }
}

# Instância de log para rastreabilidade de processos AIESEC
logger = logging.getLogger(__name__)


# =================================================================
# DECORADOR DE AUTENTICAÇÃO E CHECAGEM DE TOKEN
# =================================================================

def gerar_token_podio_rota(service: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Fábrica de Decoradores de Inspeção e Autenticação de Rota.

    Recebe o identificador do serviço e intercepta a requisição para injetar
    ou renovar o Token de Acesso do Podio de maneira otimizada via cache.

    Args:
        service (str): O identificador do serviço no CONFIG_MAP (ex: "new-lead-ogx").

    Returns:
        Callable: O decorador de rota configurado.
    """

    # Este é o decorador real que recebe a função de controle (View Function) do Flask
    def decorador(f: Callable[..., Any]) -> Callable[..., Any]:

        # O @wraps preserva o nome, as docstrings e os metadados da função original 'f'
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            try:
                # Log indicando o início da interceptação para o serviço configurado
                logger.info(f"AIESEC Auth | Interceptando rota para o serviço: {service}")

                # Busca o dicionário de configurações com base no parâmetro "service"
                config: Dict[str, str | Dict[str, Any]] | None = CONFIG_MAP.get(service)

                # Se o serviço não estiver registrado no CONFIG_MAP, barra a requisição de imediato
                if not config:
                    logger.error(f"AIESEC Auth | Serviço '{service}' não configurado no CONFIG_MAP.")
                    raise ValueError(f"Configuração não encontrada para o serviço: {service}")

                logger.info(f"AIESEC Auth | Validando token para: {service}")

                # --- ESTRATÉGIA CACHE-ASIDE (RESOLUÇÃO SÍNCRONA) ---
                # Como o gerenciador de cache opera sobre corotinas assíncronas (async def),
                # e este decorador do middleware é estritamente síncrono, utilizamos
                # `async_to_sync` para bloquear temporariamente a execução da thread de forma segura,
                # resolvendo o token antes de entregar a requisição ao Flask-OpenAPI3.
                async_to_sync(cache.get_or_set)(
                    key=config["key"],
                    fetch=lambda: getAcessToken(config["credenciais"]),
                    baixando=f"Chave de Acesso ao Podio ({service})",
                    CACHE_TLL=900  # tempo de duração do cache do acess token
                )

                logger.info(f"AIESEC Auth | Token validado com sucesso para {service}.")

            # Captura erros de configuração ausente ou inválida
            except ValueError as ve:
                logger.error(f"AIESEC Auth Error | {str(ve)}")
                raise ve

            # Captura falhas de conexão com o Podio, problemas no cache ou outras exceções imprevistas
            except Exception as e:
                logger.error(f"AIESEC Critical Error | Falha na autenticação do Podio: {str(e)}")
                raise e

            # Se o token estiver ativo e atualizado, executa a lógica principal da rota original
            return f(*args, **kwargs)

        # Retorna a função interna interceptora embrulhada
        return decorated_function

    # Retorna o decorador customizado pronto para uso
    return decorador


# =================================================================
# EXPORTAÇÕES DO MÓDULO
# =================================================================
__all__ = ["gerar_token_podio_rota"]