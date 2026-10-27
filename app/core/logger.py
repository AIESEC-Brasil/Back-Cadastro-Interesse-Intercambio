"""Configuração dos logs da aplicação e do servidor HTTP."""

from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from typing import Self
from zoneinfo import ZoneInfo

# ==============================================================================
# PADRÕES E HANDLERS DE LOGGING
# ==============================================================================
LOG_DIR: str = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "logs")
)
TIMEZONE: ZoneInfo = ZoneInfo("America/Sao_Paulo")
LOG_FORMAT: str = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT: str = "%d/%m/%Y %H:%M:%S"

_file_handler: FlushHandler | None = None
_console_handler: logging.StreamHandler | None = None


class FlushHandler(TimedRotatingFileHandler):
    """Grava cada registro no arquivo imediatamente."""

    def emit(self: Self, record: logging.LogRecord) -> None:
        """Grava o registro e descarrega o buffer para mantê-lo disponível."""
        super().emit(record)
        self.flush()


def _brasil_timestamp(seconds: float | None) -> time.struct_time:
    """Converte o horário do registro para o fuso nacional de São Paulo."""
    timestamp: float = time.time() if seconds is None else seconds
    return datetime.fromtimestamp(timestamp, TIMEZONE).timetuple()


def _get_file_handler(formatter: logging.Formatter) -> FlushHandler:
    """Cria uma vez e configura o handler diário do arquivo de log."""
    global _file_handler
    if _file_handler is None:
        _file_handler = FlushHandler(
            os.path.join(LOG_DIR, "app.log"),
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8",
        )
        _file_handler.suffix = "%Y-%m-%d.log"
    _file_handler.setFormatter(formatter)
    return _file_handler


def _get_console_handler(formatter: logging.Formatter) -> logging.StreamHandler:
    """Cria uma vez e configura o handler de saída padrão do terminal."""
    global _console_handler
    if _console_handler is None:
        _console_handler = logging.StreamHandler(sys.stdout)
    _console_handler.setFormatter(formatter)
    return _console_handler


def setup_logging(debug: bool = False) -> None:
    """Grava logs da aplicação no arquivo e amplia a saída no modo debug."""
    os.makedirs(LOG_DIR, exist_ok=True)

    formatter: logging.Formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    formatter.converter = _brasil_timestamp

    file_handler: FlushHandler = _get_file_handler(formatter)
    console_handler: logging.StreamHandler = _get_console_handler(formatter)

    app_logger: logging.Logger = logging.getLogger("app")
    app_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    app_logger.propagate = False
    if file_handler not in app_logger.handlers:
        app_logger.addHandler(file_handler)
    if debug and console_handler not in app_logger.handlers:
        app_logger.addHandler(console_handler)
    elif not debug and console_handler in app_logger.handlers:
        app_logger.removeHandler(console_handler)

    endpoint_logger: logging.Logger = logging.getLogger(
        "app.middlewares.registrando_endpoint"
    )
    endpoint_logger.setLevel(logging.INFO)
    endpoint_logger.propagate = False
    if file_handler not in endpoint_logger.handlers:
        endpoint_logger.addHandler(file_handler)
    if console_handler in endpoint_logger.handlers:
        endpoint_logger.removeHandler(console_handler)

    werkzeug_logger: logging.Logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    werkzeug_logger.propagate = False
    if console_handler not in werkzeug_logger.handlers:
        werkzeug_logger.addHandler(console_handler)

    warnings_logger: logging.Logger = logging.getLogger("py.warnings")
    warnings_logger.setLevel(logging.WARNING)
    warnings_logger.propagate = False
    if file_handler not in warnings_logger.handlers:
        warnings_logger.addHandler(file_handler)
    if debug and console_handler not in warnings_logger.handlers:
        warnings_logger.addHandler(console_handler)
    elif not debug and console_handler in warnings_logger.handlers:
        warnings_logger.removeHandler(console_handler)
    logging.captureWarnings(True)


__all__ = ["LOG_DIR", "setup_logging"]
