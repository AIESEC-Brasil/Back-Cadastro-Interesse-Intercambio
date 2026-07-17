"""
Configuração de logging da aplicação, incluindo:
- Logger 'app' com rotação diária e flush imediato a cada mensagem
- Logger 'audit' com rotação e contexto de requisição (IP, usuário, request_id)
- Logger 'werkzeug' direcionado ao console para evitar duplicação
"""
import logging  # Biblioteca padrão de logging do Python
import os       # Manipulação de diretórios e caminhos
import sys      # Acesso a fluxos do sistema (stdout)
from logging.handlers import TimedRotatingFileHandler # Handler para rotação de arquivos por tempo
from ..utils import logging_time_brasil # Utilitário customizado para fuso horário brasileiro

# =================================================================
# MAPEAMENTO DE DIRETÓRIOS
# =================================================================

# 1. Caminho absoluto do diretório onde este arquivo reside
diretorio_atual = os.path.dirname(os.path.abspath(__file__))

# 2. Identifica a raiz do projeto (sobe 2 níveis)
raiz_projeto = os.path.abspath(os.path.join(diretorio_atual, "..", ".."))

# 3. Define onde a pasta 'logs' será criada/utilizada na raiz
LOG_DIR = os.path.join(raiz_projeto, "logs")

# =================================================================
# COMPONENTES DE SUPORTE
# =================================================================

class RequestContextFilter(logging.Filter):
    """
    Filtro que injeta dados dinâmicos do Flask em cada linha de log.
    Permite rastrear o IP, ID da requisição e o Usuário logado.
    """
    def filter(self, record):
        try:
            from flask import request, g
            # Tenta capturar dados do contexto ativo do Flask
            record.ip = request.remote_addr if request else "-"
            record.request_id = getattr(g, "request_id", "-")
            record.user_id = getattr(g, "user_id", "-")
        except Exception:
            # Fallback caso o log ocorra fora de uma requisição HTTP
            record.ip = "-"
            record.request_id = "-"
            record.user_id = "-"
        return True

class FlushHandler(TimedRotatingFileHandler):
    """
    Handler customizado que desativa o buffering do sistema operacional.
    Garante que a mensagem seja escrita no disco imediatamente após o evento.
    """
    def emit(self, record):
        super().emit(record)
        self.flush() # Força a persistência física no disco

# =================================================================
# CONFIGURAÇÃO PRINCIPAL
# =================================================================



def setup_logging():
    """Configura handlers/formatters dos loggers 'app', 'audit' e 'werkzeug'."""
    # Garante que a pasta de logs exista
    os.makedirs(LOG_DIR, exist_ok=True)

    # -------- FORMATOS E TZ --------
    # Sobrescreve o conversor de tempo para usar o horário do Brasil
    logging.Formatter.converter = logging_time_brasil

    # Formato padrão para logs de erro/aplicação
    APP_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    # Formato enriquecido para trilha de auditoria
    AUDIT_FORMAT = "%(asctime)s | AUDIT | %(name)s | IP=%(ip)s | USER=%(user_id)s | REQ=%(request_id)s | %(message)s"

    app_formatter = logging.Formatter(APP_FORMAT)
    audit_formatter = logging.Formatter(AUDIT_FORMAT)

    # ---------- LOGGER DO APP ----------
    root = logging.getLogger("app")
    root.setLevel(logging.INFO)
    root.propagate = False # Impede que logs do app "vazem" para o logger root global

    # Handler de arquivo com rotação diária (meia-noite)
    app_handler = FlushHandler(
        os.path.join(LOG_DIR, "app.log"),
        when="midnight",
        interval=1,
        backupCount=30, # Mantém histórico dos últimos 30 dias
        encoding="utf-8",
    )
    app_handler.suffix = "%Y-%m-%d.log"
    app_handler.setFormatter(app_formatter)
    app_handler.addFilter(RequestContextFilter())

    # Handler de console para monitoramento em tempo real via terminal
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(app_formatter)

    # Vincula os handlers ao logger "app" se não estiverem presentes
    if not root.handlers:
        root.addHandler(app_handler)
        root.addHandler(console_handler)

    # ---------- LOGGER DO FLASK (WERKZEUG) ----------
    # Configurado para aparecer apenas no terminal para não poluir o app.log
    flask_logger = logging.getLogger("werkzeug")
    if not flask_logger.handlers:
        flask_logger.addHandler(console_handler)
        flask_logger.propagate = False

__all__ = ["setup_logging"]