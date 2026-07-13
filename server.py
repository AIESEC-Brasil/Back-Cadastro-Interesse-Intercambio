"""
Ponto de entrada do servidor.

- Carrega variáveis de ambiente (.env)
- Configura logging
- Inicializa a aplicação Flask
- Executa com app.run (desenvolvimento) ou waitress (produção)
"""

# ==============================
# Importações (Dependencies)
# ==============================
import os # Biblioteca para manipulação de arquivos e caminhos do sistema operacional
from dotenv import load_dotenv # Utilitário para carregar variáveis de ambiente de um arquivo .env

# ==============================
# Configuração de Ambiente
# ==============================

# Localiza o diretório absoluto onde este arquivo (run.py/main.py) está residindo
path_atual = os.path.dirname(os.path.abspath(__file__))

# Concatena o caminho do diretório com o arquivo '.env' e carrega as variáveis na memória do sistema
load_dotenv(os.path.join(path_atual, ".env.test"))

# ==============================
# Inicialização do Sistema
# ==============================

# Importação de utilitários internos após o carregamento do .env (necessário para as configs funcionarem)
from app.core import setup_logging, IS_DEV,IS_TEST,configurar_idioma

configurar_idioma()
# Configura o formato de saída, níveis (INFO/DEBUG) e destinos dos logs da aplicação
setup_logging()

# Importa a fábrica da aplicação e o servidor WSGI de produção
from app import create_app
from waitress import serve

# Inicializa a instância da aplicação Flask com todas as configurações, rotas e middlewares
app = create_app()

# ==============================
# Execução do Servidor
# ==============================

if __name__ == "__main__":
    # Verifica se o ambiente NÃO é de produção (ex: development, testing)
    if IS_DEV:
        # Roda o servidor interno do Flask, ideal para debug (reinicia ao alterar código)
        app.run(debug=True,host="127.0.0.1",port=5000)
    elif IS_TEST:
        serve(app, host="0.0.0.0", port=5000)
    else:
        # Roda o servidor Waitress, um servidor WSGI robusto para ambientes produtivos
        # host="0.0.0.0" permite conexões externas ao servidor
        serve(app, host="0.0.0.0", port=5000)