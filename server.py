"""Ponto de entrada principal do servidor de aplicação.

Este módulo orquestra a inicialização da aplicação executando as seguintes etapas:
1. Carrega as variáveis de ambiente a partir do arquivo `.env.dev`.
2. Configura a localização/idioma e o sistema de logging global.
3. Inicializa a instância da aplicação Flask via Application Factory (`create_app`).
4. Executa o servidor de desenvolvimento interno do Flask ou o servidor WSGI
   de alta performance Waitress, dependendo do ambiente (`IS_DEV`, `IS_TEST`, `PROD`).
"""

# =================================================================
# 1. IMPORTAÇÕES E CONFIGURAÇÃO DE AMBIENTE
# =================================================================
import os  # Utilitário para manipulação do sistema operacional e caminhos de arquivo
from dotenv import load_dotenv  # Biblioteca para carregar variáveis de ambiente de arquivos .env

# Localiza o caminho absoluto do diretório onde este script está sendo executado
path_atual = os.path.dirname(os.path.abspath(__file__))

# Concatena o caminho absoluto com o arquivo '.env.dev' e injeta as variáveis no os.environ
load_dotenv(os.path.join(path_atual, ".env.dev"))

# =================================================================
# 2. INICIALIZAÇÃO DE RECURSOS CORE
# =================================================================
# Importações relativas de módulos internos (devem ocorrer obrigatoriamente após a carga do .env)
from app import create_app  # Fábrica da aplicação Flask/OpenAPI
from app.core import (
    IS_DEV,             # Booleano indicando se o ambiente é de desenvolvimento
    IS_TEST,            # Booleano indicando se o ambiente é de testes
    configurar_idioma,  # Configura preferências regionais e locale do sistema
    setup_logging,      # Configura handlers, formatação e níveis do logger
)
from waitress import serve  # Servidor WSGI robusto e multithread para produção/testes

# Configura o locale e preferências regionais da aplicação
configurar_idioma()

# Configura os logs globais da aplicação conforme o ambiente carregado
setup_logging()

# Inicializa a aplicação Flask com todas as extensões, rotas e middlewares registrados
app = create_app()


# =================================================================
# 3. EXECUÇÃO DO SERVIDOR WSGI / DEV
# =================================================================
if __name__ == "__main__":
    if IS_DEV:
        # Executa o servidor nativo do Flask com auto-reload ativado (apenas para desenvolvimento)
        app.run(debug=True, host="127.0.0.1", port=5000)

    elif IS_TEST:
        # Executa o servidor Waitress configurado para ambiente de homologação/testes
        serve(app, host="0.0.0.0", port=5000, threads=5)

    else:
        # Executa o servidor Waitress pronto para produção (aceita conexões externas via 0.0.0.0)
        serve(app, host="0.0.0.0", port=5000, threads=5)