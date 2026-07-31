"""Módulo de Automação de Migrações.

Gerencia a criação de tabelas, controle de versão do esquema e sincronização
entre os modelos SQLAlchemy e o banco de dados via CLI ou inicialização automática.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import logging  # Registro de logs das operações de banco de dados
import os  # Interação com o sistema de arquivos
import sys  # Acesso aos argumentos passados via terminal (CLI)

# Componentes do Flask-Migrate para manipulação das versões do banco
from flask_migrate import downgrade, init, migrate, upgrade

from app.utils import gerar_sql_seed  # Utilitário para gerar scripts SQL de seed


# =================================================================
# 2. ORQUESTRADOR DE MIGRAÇÃO
# =================================================================

def migration() -> None:
    """Gerencia o estado do esquema do banco de dados.

    A função realiza três tarefas principais:
    1. Setup Automático: Cria o ambiente de migrações caso seja a primeira execução.
    2. Interface CLI: Escuta comandos 'migrate', 'upgrade' ou 'downgrade' vindos do terminal.
    3. Versionamento: Garante que o banco esteja na última revisão disponível.

    Returns:
        None
    """
    # 1. Capturando argumentos do terminal (ex: python app.py upgrade)
    args = sys.argv

    # 2. Localização lógica do projeto
    # Garante que a pasta 'migrations' fique na raiz, independente de onde o script é chamado
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    raiz_projeto = os.path.abspath(os.path.join(diretorio_atual, "..", ".."))
    migrations_dir = os.path.join(raiz_projeto, "migrations")

    # 3. Instanciando o Logger para monitoramento
    logger = logging.getLogger(__name__)

    # ---------- 1. Inicialização Automática (First Run) ----------
    # Se a pasta 'migrations' não existe, o sistema prepara o banco do zero
    if not os.path.exists(migrations_dir):
        logger.info(
            f"Diretório migrations não detectado. Iniciando setup em: {migrations_dir}"
        )
        try:
            # Inicializa o repositório do Alembic
            init(directory=migrations_dir)

            # Detecta as mudanças nos modelos e gera o script inicial
            logger.info("Gerando script de migração inicial...")
            migrate(directory=migrations_dir)

            # Cria efetivamente as tabelas no banco de dados
            logger.info("Executando upgrade para criação das tabelas...")
            upgrade(directory=migrations_dir)
            gerar_sql_seed(raiz_projeto)
            logger.info("Infraestrutura de banco de dados pronta!")
        except Exception as e:
            logger.error(f"Falha crítica na inicialização do banco: {e}")
            return

    # ---------- 2. Processamento de Comandos CLI ----------
    # Permite gerenciar o banco via terminal: 'python main.py migrate'

    # Gera um novo script de migração baseado nas alterações dos Models
    if "migrate" in args:
        logger.info("Comando detectado: MIGRATE (Detectando alterações...)")
        try:
            migrate(directory=migrations_dir)
            logger.info("Script de migração gerado com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao gerar migração: {e}")

    # Aplica as migrações pendentes ao banco de dados
    elif "upgrade" in args:
        logger.info("Comando detectado: UPGRADE (Sincronizando banco...)")
        try:
            upgrade(directory=migrations_dir)
            logger.info("Banco de dados atualizado para a versão mais recente!")
        except Exception as e:
            logger.error(f"Erro ao aplicar upgrade: {e}")

    # Reverte a última alteração feita no banco
    elif "downgrade" in args:
        logger.info("Comando detectado: DOWNGRADE (Revertendo última versão...)")
        try:
            downgrade(directory=migrations_dir)
            logger.info("Downgrade concluído com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao reverter migração: {e}")


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["migration","upgrade"]