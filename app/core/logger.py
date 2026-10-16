"""Configuração dos logs da aplicação com rotação diária em horário de Brasília."""

import logging
import os
import sys
import time
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from zoneinfo import ZoneInfo

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))


def _hora_brasilia(seconds: float) -> time.struct_time:
    return datetime.fromtimestamp(seconds, ZoneInfo("America/Sao_Paulo")).timetuple()


class FlushHandler(TimedRotatingFileHandler):
    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.flush()


def setup_logging() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.Formatter.converter = staticmethod(_hora_brasilia)
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False

    if not app_logger.handlers:
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        file_handler = FlushHandler(
            os.path.join(LOG_DIR, "app.log"), when="midnight", interval=1,
            backupCount=30, encoding="utf-8",
        )
        file_handler.suffix = "%Y-%m-%d.log"
        file_handler.setFormatter(formatter)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        app_logger.addHandler(file_handler)
        app_logger.addHandler(console_handler)

    werkzeug_logger = logging.getLogger("werkzeug")
    if not werkzeug_logger.handlers:
        werkzeug_logger.addHandler(logging.StreamHandler(sys.stdout))
        werkzeug_logger.propagate = False


__all__ = ["setup_logging"]
