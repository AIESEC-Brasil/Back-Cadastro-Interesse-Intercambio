"""
Podio Auth Middleware
---------------------
Garante que cada conexão com o Podio seja autenticada e otimizada via cache.
Atua como um guardião de liderança, assegurando que o serviço correto acesse
os dados necessários com a credencial correta.
"""

# ==============================
# Importações (Dependencies)
# ==============================

# Ferramentas de Sistema e Logs
import logging                      # Registro de eventos para monitoramento e auditoria de erros

# Componentes do Framework Flask
from flask import current_app       # Acesso global às configurações da instância ativa do Flask
from werkzeug.exceptions import NotFound # Classe padrão para disparar erros 404 de forma limpa

# Recursos Internos da Aplicação
from flask import request       # Extensão do objeto request para capturar headers e caminhos
from ..clients import getAcessToken # Client responsável pelo handshake de OAuth2 com a API do Podio
from ..cache import cache           # Mecanismo de persistência temporária para otimizar performance

# Configurações de Segurança e Identidade
# Importação de credenciais sensíveis (Secrets) para os diferentes produtos AIESEC
from ..config import CLIENT_SECRET,CLIENT_ID, APP_ID, APP_TOKEN


# ==============================
# Configuração de Serviços
# ==============================

# Mapa de Atribuição: Associa o slug da URL às credenciais específicas.
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



# ==============================
# Função Principal (Middleware)
# ==============================

def verificar_rota() -> None:
    """
    Middleware de Inspeção de Rota.

    Analisa o path da requisição para identificar o serviço (OGX, PSEL, etc)
    e garante que um token válido do Podio esteja disponível no cache.
    """
    # 1. Extração do caminho da URL (ex: /api/v1/new-lead-ogx/...)
    path: str = request.path

    # 2. Segmentação do path para identificação do serviço
    parts: list[str] = path.strip("/").split("/")

    # 3. Bind do Adapter para validação manual de rota no contexto da aplicação
    adapter = current_app.url_map.bind("api.meu-site.com")

    try:
        logger.info(f"AIESEC Middleware | Verificando endpoint: {path}")

        # 4. Validação de Existência (Match):
        # Garante que a URL e o Método existam no mapa de rotas.
        adapter.match(path, method=request.method)

        # 5. Identificação do Serviço (Estratégia de Segmento):
        # O serviço é identificado no índice 0 da rota (/new-lead-ogx/...)
        if len(parts) >= 2:
            service_name: str = parts[0]

            # 6. Recuperação de Configuração
            config: dict = CONFIG_MAP.get(service_name)

            if config:
                logger.info(f"AIESEC Auth | Validando token para: {service_name}")

                # 7. Estratégia de Cache (Lazy Loading):
                # Otimiza o tempo de resposta e evita o rate limit da API do Podio.
                cache.get_or_set(
                    key=config["key"],
                    fetch=lambda: getAcessToken(config["credenciais"]),
                    baixando="Chave de Acesso ao Podio"
                )
                logger.info(f"AIESEC Auth | Token validado para {service_name}.")

            logger.info("AIESEC Middleware | Validação concluída com sucesso.")

        # 8. Tratamento de Exceções de Documentação e Estáticos
        # Permite o acesso livre a rotas de documentação técnica
        elif parts[1] in ["docs","register"] or parts[0] in ["apidoc","openapi","static"]:
            return None
        else:
            logger.warning(f"AIESEC Middleware | Endpoint genérico acessado: {path}")

        return None

    except NotFound:
        logger.error(f"AIESEC 404 | Endpoint '{path}' inexistente ou método proibido.")
        raise NotFound(f"O recurso {path} não foi encontrado no servidor.")

    except ValueError as ve:
        mensagem: str = f"Inconsistência de valores na rota {path}: {str(ve)}"
        logger.error(mensagem)
        raise ValueError(mensagem)

    except Exception as e:
        logger.error(f"AIESEC Critical Error | Falha no middleware: {str(e)}")
        raise e

# ==============================
# Exportações do Módulo
# ==============================
__all__ = ["verificar_rota"]