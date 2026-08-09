"""Fábrica da aplicação Flask (OpenAPI).

Configuração de CORS, banco de dados, migrações, documentação OpenAPI3,
middlewares de segurança/auditoria e registro de rotas.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import asyncio  # Biblioteca nativa para execução de loops de eventos assíncronos
import logging  # Registro de eventos para monitoramento do ciclo de vida da aplicação

from flask_cors import CORS  # Gerenciamento de permissões de acesso entre domínios (CORS)
from flask_openapi3 import Info, OpenAPI  # Extensão Flask para documentação e validação automática OpenAPI/Swagger

from .api import api  # Árvore de rotas principal (Blueprints) do projeto
from .controller import divisao_mercado, new_lead_ogx  # Roteadores especializados de negócio
from .core import (
    AMBIENTE,                          # String identificadora do ambiente de execução (ex: prod, dev)
    DB_CONNECT,                        # String de conexão com o banco de dados relacional
    DB_POOL_PRE_PING,                  # <--- Validação de conexões ociosas
    DB_POOL_RECYCLE,                   # <--- Intervalo de reciclagem do pool
    compress,                          # Instância global do otimizador de compressão de respostas
    db,                                # Instância do SQLAlchemy ORM
    ma,                                # Instância do Marshmallow para serialização
    migrate,                           # Instância do Flask-Migrate
    pre_carregamento_metadados,        # Função assíncrona para aquecimento de cache de metadados
)
from .manager import migration  # Função orquestradora de migrações no banco de dados
from .middlewares import register_url, verificar_origem  # Middlewares de auditoria e interceptação
from .model import db as model_db  # Garantia de registro dos modelos ORM para detecção no Flask-Migrate
from .utils import handle_validation_error, handle_app_error, converter_resposta_dinamica  # Handler customizado para erros
from .dto import AppError

# =================================================================
# 2. APPLICATION FACTORY
# =================================================================

def create_app() -> OpenAPI:
    """Inicializa e configura a aplicação Flask utilizando o padrão Application Factory.

    Processos realizados:
    - Instancia o objeto OpenAPI com metadados da API e handlers de validação.
    - Configura e ativa a compressão de respostas HTTP (Gzip/Brotli).
    - Configura políticas de CORS para liberar headers e origens externas.
    - Configura e inicializa as extensões de persistência (SQLAlchemy, Marshmallow, Flask-Migrate).
    - Executa automaticamente as migrações pendentes no esquema do banco de dados.
    - Injeta middlewares de segurança (before_request) e auditoria (after_request).
    - Registra as Blueprints e roteadores de endpoints da API.
    - Executa o pré-carregamento assíncrono dos metadados do Podio no contexto da aplicação.

    Returns:
        OpenAPI: Uma instância configurada da aplicação Flask pronta para execução.

    Raises:
        Exception: Caso ocorra uma falha crítica na conexão com o banco ou na inicialização.
    """
    # Inicializa o logger para capturar eventos durante o startup do servidor
    logger = logging.getLogger(__name__)

    try:
        logger.info("Servidor iniciando...")
        logger.info(f"AMBIENTE: {AMBIENTE}")

        # Instanciação da aplicação Flask com suporte nativo à especificação OpenAPI 3
        app = OpenAPI(
            __name__,
            info=Info(title="API", version="2.0.0"),
            validate_response=True,  # Valida se o formato do JSON retornado bate com a documentação
            validation_error_status=422,  # Código HTTP retornado em falhas de esquema no payload
            validation_error_callback=handle_validation_error,  # Callback customizado para formatar erros de validação
            validate_response_callback=converter_resposta_dinamica  # Callback customizado para validar e personalizar o retorno
        )

        # =========================================================
        # Configuração de Compressão de Respostas
        # =========================================================
        logger.info("Ativando Compressão de Respostas...")
        # Define os tipos MIME que devem ser comprimidos antes do envio ao cliente
        app.config["COMPRESS_MIMETYPES"] = [
            "application/json",
            "text/html",
            "text/css",
            "text/xml",
            "application/javascript",
        ]
        app.config["COMPRESS_MIN_SIZE"] = 10  # Comprime qualquer payload acima de 10 bytes
        app.config["COMPRESS_LEVEL"] = 6      # Nível de compressão otimizado (balanço CPU vs tamanho)
        app.config["COMPRESS_REGISTER"] = True  # Habilita o registro automático de hooks no Flask

        # Inicializa a extensão de compressão vinculando-a ao app
        compress.init_app(app)

        # Força o compressor a ser executado no hook after_request
        app.after_request(compress.after_request)
        logger.info("Compressão de Respostas Ativada com Sucesso!")

        # =========================================================
        # Configuração de CORS (Cross-Origin Resource Sharing)
        # =========================================================
        logger.info("Permitindo Acesso de Domínios Autorizados...")
        CORS(
            app,
            origins=["*"],
            allow_headers=["X-API-KEY", "Content-Type", "ngrok-skip-browser-warning"],
            methods=["GET", "POST", "OPTIONS"],
        )
        logger.info("Domínios Autorizados Cadastrados com Sucesso!")

        # =========================================================
        # Conexão e Inicialização do Banco de Dados
        # =========================================================
        # Oculta credenciais sensíveis no log de inicialização exibindo apenas o host
        logger.info(f"Tentando conectar ao banco: {DB_CONNECT.split('@')[-1]}")
        app.config["SQLALCHEMY_DATABASE_URI"] = DB_CONNECT

        # Injeta as configurações do Pool do SQLAlchemy (Pre-Ping e Recycle)
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": DB_POOL_PRE_PING,
            "pool_recycle": DB_POOL_RECYCLE,
        }

        # Inicializa o ORM SQLAlchemy com as configurações da aplicação
        db.init_app(app)

        # Inicializa a extensão Marshmallow para serialização e desserialização de DTOs
        ma.init_app(app)

        # Inicializa o Flask-Migrate vinculado ao ORM
        migrate.init_app(app, db)

        logger.info("Banco Conectado com Sucesso!")

        # =========================================================
        # Rotinas de Migração Automática
        # =========================================================
        # Executa a orquestração de migrações dentro do contexto ativo da aplicação
        with app.app_context():
            logger.info("Entrou no contexto da aplicação. Iniciando migrações...")
            migration()
            logger.info("Migração finalizada com Sucesso!")

        # =========================================================
        # Middlewares e Registro de Endpoints
        # =========================================================
        # Middleware executado antes do processamento das rotas (validação de token/origem)
        app.before_request(verificar_origem)

        # Registro oficial da árvore de roteadores e Blueprints OpenAPI
        app.register_api(new_lead_ogx)
        app.register_api(divisao_mercado)
        app.register_api(api)
        app.register_error_handler(AppError, handle_app_error)  # Intercepta erros da classe AppError

        # Middleware executado após a conclusão da resposta (auditoria e métricas)
        app.after_request(register_url)

        logger.info("Servidor Inicializado com Sucesso!")

        # =========================================================
        # Pré-carregamento Assíncrono de Metadados
        # =========================================================
        # Carrega em cache os metadados do Podio antes de disponibilizar o aceite de requisições
        with app.app_context():
            asyncio.run(pre_carregamento_metadados())

        return app

    except Exception as e:
        # Registra o erro no log e interrompe a inicialização para evitar um estado inconsistente
        logger.error(f"FALHA CRÍTICA NO STARTUP: {str(e)}")
        raise e


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["create_app"]