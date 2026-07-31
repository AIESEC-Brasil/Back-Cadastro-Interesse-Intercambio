"""Configuração de logging da aplicação.

Inclui:
- Logger 'app' com rotação diária e flush imediato a cada mensagem
- Logger 'audit' com rotação e contexto de requisição (IP, usuário, request_id)
- Logger 'werkzeug' direcionado ao console para evitar duplicação
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import logging  # Biblioteca padrão de logging do Python
import os  # Manipulação de diretórios e caminhos
import sys  # Acesso a fluxos do sistema (stdout)
# Handler para rotação de arquivos por tempo
from logging.handlers import TimedRotatingFileHandler

# Utilitário customizado para fuso horário brasileiro
from ..utils import logging_time_brasil

# =================================================================
# 2. MAPEAMENTO DE DIRETÓRIOS
# =================================================================

# Caminho absoluto do diretório onde este arquivo reside
diretorio_atual = os.path.dirname(os.path.abspath(__file__))

# Identifica a raiz do projeto (sobe 2 níveis)
raiz_projeto = os.path.abspath(os.path.join(diretorio_atual, "..", ".."))

# Define onde a pasta 'logs' será criada/utilizada na raiz do projeto
LOG_DIR = os.path.join(raiz_projeto, "logs")


# =================================================================
# 3. COMPONENTES DE SUPORTE E HANDLERS CUSTOMIZADOS
# =================================================================

class RequestContextFilter(logging.Filter):
    """Filtro que injeta dados dinâmicos do Flask em cada linha de log.

    Permite rastrear o IP, ID da requisição e o ID do Usuário logado.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Adiciona atributos de contexto do Flask ao registro de log.

        Args:
            record (logging.LogRecord): Registro do log sendo processado.

        Returns:
            bool: Sempre True para autorizar a emissão do log.
        """
        try:
            from flask import g, request

            # Tenta capturar dados do contexto ativo do Flask
            record.ip = request.remote_addr if request else "-"
            record.request_id = getattr(g, "request_id", "-")
            record.user_id = getattr(g, "user_id", "-")
        except (RuntimeError, AttributeError):
            # Fallback executado se o log ocorrer fora de um contexto HTTP
            record.ip = "-"
            record.request_id = "-"
            record.user_id = "-"
        return True


class FlushHandler(TimedRotatingFileHandler):
    """Handler customizado que desativa o buffering do sistema operacional.

    Garante que a mensagem seja escrita no disco imediatamente após o evento.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Força a liberação do buffer do arquivo após emitir o registro."""
        super().emit(record)
        self.flush()  # Força a persistência física no disco


# =================================================================
# 4. CONFIGURAÇÃO PRINCIPAL
# =================================================================

def setup_logging() -> None:
    """Configura handlers e formatters dos loggers 'app', 'audit' e 'werkzeug'."""
    # Garante que a pasta de logs exista no sistema de arquivos
    os.makedirs(LOG_DIR, exist_ok=True)

    # -------- FORMATOS E FUSO HORÁRIO --------
    # Sobrescreve o conversor de tempo para usar o fuso do Brasil
    logging.Formatter.converter = logging_time_brasil

    # Formato padrão para logs de erro e aplicação
    APP_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    # Formato enriquecido para trilha de auditoria
    AUDIT_FORMAT = (
        "%(asctime)s | AUDIT | %(name)s | IP=%(ip)s | "
        "USER=%(user_id)s | REQ=%(request_id)s | %(message)s"
    )

    app_formatter = logging.Formatter(APP_FORMAT)
    audit_formatter = logging.Formatter(AUDIT_FORMAT)

    # ---------- LOGGER PRINCIPAL DA APLICAÇÃO ----------
    root = logging.getLogger("app")
    root.setLevel(logging.INFO)
    root.propagate = False  # Impede que logs do app "vazem" para o logger root

    # Handler de arquivo com rotação diária (meia-noite)
    app_handler = FlushHandler(
        os.path.join(LOG_DIR, "app.log"),
        when="midnight",
        interval=1,
        backupCount=30,  # Mantém histórico dos últimos 30 dias
        encoding="utf-8",
    )
    app_handler.suffix = "%Y-%m-%d.log"
    app_handler.setFormatter(app_formatter)
    app_handler.addFilter(RequestContextFilter())

    # Handler de console para monitoramento via terminal
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(app_formatter)

    # Vincula os handlers ao logger "app" se ainda não estiverem configurados
    if not root.handlers:
        root.addHandler(app_handler)
        root.addHandler(console_handler)

    # ---------- LOGGER DO FLASK / WERKZEUG ----------
    # Configurado para aparecer apenas no terminal para não poluir o app.log
    flask_logger = logging.getLogger("werkzeug")
    if not flask_logger.handlers:
        flask_logger.addHandler(console_handler)
        flask_logger.propagate = False


# =================================================================
# 5. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["setup_logging"]