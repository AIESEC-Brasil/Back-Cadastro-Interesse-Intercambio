"""Cache em memória para os metadados do Apps Script B2C."""

import asyncio
import copy
import inspect
import logging
import threading
import time
from typing import Any, Callable

import httpx

from ..config import CACHE_TTL
from ..dto import HttpStatus

logger = logging.getLogger(__name__)


def _status_name(status: int) -> str:
    """Converte um código HTTP para o nome do enum, com fallback desconhecido."""
    try:
        return HttpStatus(status).name
    except ValueError:
        return "UNKNOWN"


class CacheManager:
    """Armazena dados com TTL, timestamp e sincronização de cargas concorrentes."""

    def __init__(self) -> None:
        """Inicializa o armazenamento e os locks por event loop e chave."""
        self.store: dict[str, dict[str, Any]] = {}
        self._locks: dict[asyncio.AbstractEventLoop, dict[str, asyncio.Lock]] = {}
        self._locks_guard = threading.Lock()

    def _get_lock(self, key: str) -> asyncio.Lock:
        """Obtém o lock da chave no event loop atualmente em execução."""
        loop = asyncio.get_running_loop()
        with self._locks_guard:
            loop_locks = self._locks.setdefault(loop, {})
            if key not in loop_locks:
                loop_locks[key] = asyncio.Lock()
            return loop_locks[key]

    def _get_valid_entry(self, key: str, ttl: int) -> dict[str, Any] | None:
        """Retorna a entrada se ela existir e ainda estiver dentro do TTL."""
        cached = self.store.get(key)
        if cached and time.time() - cached["timestamp"] < ttl:
            return cached
        return None

    @staticmethod
    def _normalize(payload: Any) -> dict[str, Any] | None:
        """Normaliza o envelope B2C e remove apenas opções explicitamente inativas.

        Retorna ``None`` quando o payload não contém uma lista ``fields`` válida.
        Uma cópia profunda evita modificar o objeto recebido do cliente HTTP.
        """
        if not isinstance(payload, dict):
            return None

        root = copy.deepcopy(payload)
        data = root.get("data", root)
        if not isinstance(data, dict) or not isinstance(data.get("fields"), list):
            return None

        fields = []
        for field in data["fields"]:
            if not isinstance(field, dict):
                continue
            config = field.get("config")
            if not isinstance(config, dict):
                config = {}
            settings = config.get("settings")
            if not isinstance(settings, dict):
                settings = {}
            options = settings.get("options") or settings.get("possible_types") or []
            if not isinstance(options, list):
                options = []
            settings["options"] = [
                option
                for option in options
                if not isinstance(option, dict)
                or option.get("status") in (None, "activate", "active")
            ]
            config["settings"] = settings
            field["config"] = config
            fields.append(field)

        return {"data": {"fields": fields}}

    async def get_or_set(
        self,
        key: str,
        fetch: Callable[[], Any] | None = None,
        ttl: int | None = None,
        resync: bool = False,
        baixando: str | None = None,
    ) -> tuple[Any, int]:
        """Retorna dados em cache ou busca, normaliza e armazena novos metadados.

        Args:
            key: Identificador da entrada armazenada.
            fetch: Função síncrona ou assíncrona que consulta a origem dos dados.
            ttl: Validade da entrada em segundos; usa ``CACHE_TTL`` quando omitido.
            resync: Ignora a entrada atual e força uma consulta à origem.
            baixando: Nome legível usado nas mensagens de log.

        Returns:
            Tupla com o payload e o código HTTP correspondente.
        """
        ttl = CACHE_TTL if ttl is None else ttl
        label = baixando or key

        if not resync:
            cached = self._get_valid_entry(key, ttl)
            if cached:
                logger.info("AIESEC Cache | HIT: '%s' recuperado da memória", label)
                return cached["data"], 200

        if fetch is None:
            logger.warning("AIESEC Cache | MISS: '%s' sem função de busca", label)
            return {"error": f"Dados de '{label}' não estão em cache."}, 404

        # Um lock por chave evita consultas duplicadas quando várias requisições
        # encontram o mesmo cache expirado ao mesmo tempo.
        async with self._get_lock(key):
            # Confere novamente após aguardar o lock: outra requisição pode ter
            # preenchido o cache enquanto esta aguardava.
            if not resync:
                cached = self._get_valid_entry(key, ttl)
                if cached:
                    logger.info("AIESEC Cache | HIT pós-lock: '%s'", label)
                    return cached["data"], 200

            action = "FORCED RESYNC" if resync else "MISS"
            logger.info("AIESEC Cache | %s: buscando '%s'", action, label)

            try:
                result = fetch()
                if inspect.isawaitable(result):
                    result = await result
            except (TimeoutError, httpx.TimeoutException):
                logger.exception(
                    "AIESEC Cache | timeout ao buscar '%s' | HTTP %s %s",
                    label,
                    HttpStatus.GATEWAY_TIMEOUT.value,
                    HttpStatus.GATEWAY_TIMEOUT.name,
                )
                return (
                    {"error": f"Tempo limite ao buscar '{label}'."},
                    HttpStatus.GATEWAY_TIMEOUT,
                )
            except Exception:
                logger.exception(
                    "AIESEC Cache | erro ao buscar '%s' | HTTP %s %s",
                    label,
                    HttpStatus.BAD_GATEWAY.value,
                    HttpStatus.BAD_GATEWAY.name,
                )
                return (
                    {"error": f"Falha ao consultar a fonte de '{label}'."},
                    HttpStatus.BAD_GATEWAY,
                )

            if (
                isinstance(result, tuple)
                and len(result) == 2
                and isinstance(result[0], int)
            ):
                status, payload = result
            else:
                status, payload = 200, result

            if not 200 <= status < 300:
                log = logger.error if status >= 500 else logger.warning
                log(
                    "AIESEC Cache | busca de '%s' falhou | HTTP %s %s",
                    label,
                    status,
                    _status_name(status),
                )
                return payload, status

            data = self._normalize(payload)
            if data is None:
                logger.error(
                    "AIESEC Cache | payload inválido para '%s' | HTTP %s %s",
                    label,
                    HttpStatus.BAD_GATEWAY.value,
                    HttpStatus.BAD_GATEWAY.name,
                )
                return (
                    {"error": "Formato de metadados inválido."},
                    HttpStatus.BAD_GATEWAY,
                )

            self.store[key] = {"data": data, "timestamp": time.time()}
            logger.info("AIESEC Cache | '%s' armazenado", label)
            return data, status


cache = CacheManager()

__all__ = ["cache", "CacheManager"]
