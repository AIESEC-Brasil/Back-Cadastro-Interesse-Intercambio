"""Módulo de Infraestrutura: AIESEC Security - Podio Auth Middleware.

Garante que cada conexão com o Podio seja autenticada e otimizada via cache.
Atua como um guardião, assegurando que o serviço correto acesse os dados
necessários com as credenciais OAuth2 adequadas.

Para garantir compatibilidade com rotas síncronas e evitar problemas de validação
no Flask-OpenAPI3, este middleware resolve as chamadas assíncronas do gerenciador
de cache de forma síncrona segura utilizando a ponte `async_to_sync`.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================

# Ferramentas de Sistema e Logs
from functools import wraps  # Preserva os metadados da função original decorada
import logging  # Registro de eventos para auditoria de segurança
from datetime import timedelta # Módulo nativo para manipulação e cálculos de datas e horários
# Conversor de contexto Assíncrono para Síncrono
from asgiref.sync import async_to_sync

# Utilitários de Tipagem Estática
from typing import Any, Callable, Dict, Union

# Recursos Internos da Aplicação
from ..cache import cache  # Persistência temporária em memória para otimização
from ..clients import (  # Handshake de OAuth2 com a API do Podio
    get_access_token,
)

# Configurações de Segurança e Identidade (Secrets)
from ..config import APP_ID, APP_TOKEN, CLIENT_ID, CLIENT_SECRET

# =================================================================
# 2. CONFIGURAÇÃO DE SERVIÇOS (CONFIG_MAP)
# =================================================================
# Mapa de Atribuição: Associa o identificador do serviço às credenciais específicas.
CONFIG_MAP: Dict[str, Dict[str, Any]] = {
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

# Instância do logger para rastreabilidade de processos AIESEC
logger = logging.getLogger(__name__)


# =================================================================
# 3. DECORADOR DE AUTENTICAÇÃO E CHECAGEM DE TOKEN
# =================================================================

def gerar_token_podio_rota(
        service: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Fábrica de Decoradores de Inspeção e Autenticação de Rota.

    Recebe o identificador do serviço e intercepta a requisição para injetar
    ou renovar o Token de Acesso do Podio de maneira otimizada via cache.

    Args:
        service (str): O identificador do serviço no CONFIG_MAP (ex: "new-lead-ogx").

    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: O decorador de rota configurado.
    """

    # Decorador real que recebe a função de controle (View Function) do Flask
    def decorador(f: Callable[..., Any]) -> Callable[..., Any]:

        # Preserva nome, docstring e metadados da função original 'f'
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            try:
                # Log indicando o início da interceptação para o serviço
                logger.info(
                    f"AIESEC Auth | Interceptando rota para o serviço: {service}"
                )

                # Busca o dicionário de configurações com base no parâmetro "service"
                config = CONFIG_MAP.get(service)

                # Se o serviço não estiver registrado, interrompe a requisição
                if not config:
                    logger.error(
                        f"AIESEC Auth | Serviço '{service}' não configurado no CONFIG_MAP."
                    )
                    raise ValueError(
                        f"Configuração não encontrada para o serviço: {service}"
                    )

                logger.info(f"AIESEC Auth | Validando token para: {service}")

                async def _fetch_token() -> Dict[str, Any]:
                    """Obtém o token de acesso do Podio e isola o payload de dados da resposta.

                    Esta corotina atua como uma função callback interna (fetcher) para a estratégia
                    de Cache-Aside. Ela invoca o serviço de autenticação `get_access_token` e
                    assegura a normalização do retorno, extraindo unicamente o dicionário com os
                    dados do token (access_token, refresh_token, expires_in, etc.), descartando
                    quaisquer metadados de resposta HTTP (ex: tuplas com status codes ou objetos HttpStatus).

                    Adicionalmente, sanitiza qualquer atributo temporal do tipo `timedelta` convertendo-o
                    para inteiro (segundos), garantindo compatibilidade com serializações JSON.

                    Returns:
                        Dict[str, Any]: Dicionário contendo os dados sanitizados de autenticação do Podio.
                            Retorna um dicionário vazio `{}` caso a resposta não contenha uma estrutura válida.

                    Note:
                        A sanitização previne erros de serialização no cache (como
                        `TypeError: Object of type timedelta is not JSON serializable`) e falhas de
                        atributo (`AttributeError`) ao consumir o cache posteriormente.
                    """
                    resultado = await get_access_token(config["credenciais"])

                    payload: Dict[str, Any] = {}

                    # 1. Isola o dicionário se get_access_token retornar uma tupla (ex: (HttpStatus, payload) ou (200, payload))
                    if isinstance(resultado, tuple):
                        for item in resultado:
                            if isinstance(item, dict):
                                payload = item
                                break

                    # 2. Sanitiza o payload convertendo eventuais campos timedelta em segundos (int)
                    if payload:
                        payload = payload.copy()  # Evita mutar o dicionário original inesperadamente
                        for chave, valor in payload.items():
                            if isinstance(valor, timedelta):
                                payload[chave] = int(valor.total_seconds())

                    return payload

                # --- ESTRATÉGIA CACHE-ASIDE (RESOLUÇÃO SÍNCRONA) ---
                # Como o gerenciador de cache opera sobre corotinas assíncronas (async def),
                # e este decorador do middleware é estritamente síncrono, utilizamos
                # `async_to_sync` para bloquear temporariamente a execução da thread de forma segura,
                # resolvendo o token antes de entregar a requisição ao Flask-OpenAPI3.
                async_to_sync(cache.get_or_set)(
                    key=config["key"],
                    fetch=_fetch_token,
                    baixando=f"Chave de Acesso ao Podio ({service})",
                    ttl=25200,  # Tempo de duração do cache do access token (6 horas)
                )

                logger.info(
                    f"AIESEC Auth | Token validado com sucesso para {service}."
                )
                # Metadados de token do podio
                # 1. Recupera o mapa de credenciais
                config_servico = CONFIG_MAP["new-lead-ogx"]

                # 2. Busca o item armazenado no cache de forma segura (sem encadear .get())
                item_cache = cache.store.get(config_servico.get("key"),{})

                # 3. Só tenta atualizar se o item REALMENTE já existir na memória RAM
                podio = item_cache.get("data", {})
                if podio:
                    config_servico["credenciais"].update({
                        "ACCESS_TOKEN": podio.get("access_token"),
                        "EXPIRES_IN": podio.get("expires_in"),
                        "REFRESH_TOKEN": podio.get("refresh_token"),
                        "CREATED_AT": podio.get("created_at"),
                    })
            # Captura erros de configuração ausente ou inválida
            except ValueError as ve:
                logger.error(f"AIESEC Auth Error | {str(ve)}")
                raise ve

            # Captura falhas de conexão com Podio, cache ou exceções imprevistas
            except Exception as e:
                logger.error(
                    f"AIESEC Critical Error | Falha na autenticação do Podio: {str(e)}"
                )
                raise e

            # Executa a função principal da rota original após a validação do token
            return f(*args, **kwargs)

        # Retorna a função interceptora empacotada
        return decorated_function

    # Retorna o decorador customizado pronto para uso
    return decorador


# =================================================================
# 4. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["gerar_token_podio_rota"]