"""
Fábrica da aplicação Flask (OpenAPI) com configuração de CORS, banco,
Migrações, documentação, middlewares e registro de rotas.
"""

# ==============================
# Importações (Dependencies)
# ==============================
import logging  # Registro de eventos para monitoramento do ciclo de vida da app
from flask_openapi3 import OpenAPI, Info  # Extensão Flask para documentação automática OpenAPI/Swagger
from flask_cors import CORS  # Gerenciamento de permissões de acesso entre domínios (CORS)
from .middlewares import verificar_origem, verificar_rota, register_url  # Funções de interceptação
from .utils import handle_validation_error # Função de tratamento de erros de validação do OpenAPI3
from .controller import new_lead_ogx # Importa o roteador especializado para novos leads OGX
from .api import api # Importa a árvore de rotas principal (Blueprints) do projeto
from .core import compress  # Instância de compressão para otimizar respostas HTTP

def create_app() -> OpenAPI:
    """
    Inicializa e configura a aplicação Flask utilizando o padrão Factory.

    Processos realizados:
    - Instancia o objeto OpenAPI com metadados da API.
    - Carrega e registra documentação interativa via SpecTree.
    - Configura políticas de CORS para liberar headers customizados (ex: X-API-KEY).
    - Inicializa extensões de persistência (SQLAlchemy) e serialização (Marshmallow).
    - Sincroniza o esquema do banco de dados via Flask-Migrate.
    - Injeta middlewares de segurança (before_request) e auditoria (after_request).
    - Registra a árvore de rotas (Blueprints/API).

    Args:
        Nenhum parâmetro de entrada é exigido, as configurações são lidas do .env.

    Returns:
        OpenAPI: Uma instância configurada da aplicação Flask pronta para execução.

    Raises:
        Exception: Caso ocorra uma falha crítica na conexão com o banco ou inicialização.
    """

    # Inicializa o logger para capturar eventos durante o startup
    logger = logging.getLogger(__name__)

    try:
        logger.info("Servidor iniciando...")

        # Instanciação da aplicação com suporte nativo a OpenAPI 3
        app = OpenAPI(
            __name__,
            info=Info(title="API", version="1.10.0"),
            validate_response=True,  # Valida se a resposta da rota condiz com a documentação
            validation_error_status = 422,
            validation_error_callback = handle_validation_error # <-- O OpenAPI3 chama ela direto!
        )
        # ==============================
        # Configuração de Compressão
        # ==============================
        logger.info("Ativando Compressão de Respostas...")
        # Força o nível de compressão e mimetypes aceitos
        app.config["COMPRESS_MIMETYPES"] = [
            "application/json", # JSON é o principal, mas vamos comprimir também HTML, CSS, XML e JS
            "text/html", 
            "text/css", 
            "text/xml", 
            "application/javascript"
        ]
        app.config["COMPRESS_MIN_SIZE"] = 10  # Comprime qualquer coisa maior que 10 bytes (seu JSON tem 180kb!)
        app.config["COMPRESS_LEVEL"] = 10      # Balanço perfeito entre uso de CPU e compressão
        # Instancia o compressor sem registrar os hooks automáticos padrão
        app.config["COMPRESS_REGISTER"] = False # Desativa o registro automático de hooks, permitindo controle manual
        compress.init_app(app) # Inicializa o compressor, mas não registra hooks automáticos
        # Força o compressor a rodar no after_request, pegando o JSON do OpenAPI3 já pronto!
        app.after_request(compress.after_request)
        logger.info("Compressão de Respostas Ativada com Sucesso!")

        # ==========================
        # Configuração de CORS
        # ==========================
        # Permite que domínios externos consumam a API, autorizando o header X-API-KEY
        #
        logger.info("Permitindo Acesso de Domínios Autorizados...")
        CORS(app, origins=["*"],
             allow_headers=["X-API-KEY", "Content-Type", "ngrok-skip-browser-warning"],
             methods=["GET", "POST", "OPTIONS"])
        logger.info("Domínios Autorizados Cadastrados com Sucesso!")

        # ==========================
        # Middlewares (Antes da Rota)
        # ==========================
        # Validam segurança, origem e chaves de API antes de chegar no processamento principal
        app.before_request(verificar_origem)
        app.before_request(verificar_rota)

        # Registro oficial da estrutura de endpoints
        app.register_api(new_lead_ogx)
        app.register_api(api)

        logger.info("Servidor Inicializado com Sucesso!")

        # ==========================
        # Middlewares (Depois da Rota)
        # ==========================
        # Registra métricas, logs de saída ou manipula a resposta final
        app.after_request(register_url)
        for url in app.url_map.iter_rules():
            print(url.rule)

        return app

    except Exception as e:
        # Registra a falha no log e interrompe o startup para evitar estado inconsistente
        logger.error(f"FALHA CRÍTICA NO STARTUP: {str(e)}")
        raise e


# Exportação explícita da função factory
__all__ = ["create_app"]