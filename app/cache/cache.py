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

logger: logging.Logger = logging.getLogger(__name__)

_PALAVRAS_CONECTIVAS: frozenset[str] = frozenset(
    {
        "a", "à", "ao", "aos", "as", "às", "com", "contra", "da", "das",
        "de", "desde", "di", "do", "dos", "du", "dum", "duma", "dumas",
        "duns", "e", "em", "entre", "i", "na", "nas", "no", "nos", "num",
        "numa", "nuns", "numas", "o", "os", "ou", "para", "pela", "pelas",
        "pelo", "pelos", "perante", "por", "sem", "sob", "sobre", "trás",
        "u", "um", "uma", "umas", "uns",
    }
)


def capitalizar_nome(valor: str) -> str:
    """Capitaliza palavras, mantendo conectivos em minúsculas após a primeira."""
    palavras: list[str] = valor.strip().lower().split()
    if not palavras:
        return ""
    return " ".join(
        palavra if indice and palavra in _PALAVRAS_CONECTIVAS
        else palavra[0].upper() + palavra[1:]
        for indice, palavra in enumerate(palavras)
    )


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
        loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        with self._locks_guard:
            loop_locks: dict[str, asyncio.Lock] = self._locks.setdefault(loop, {})
            if key not in loop_locks:
                loop_locks[key] = asyncio.Lock()
            return loop_locks[key]

    def _get_valid_entry(self, key: str, ttl: int) -> dict[str, Any] | None:
        """Retorna a entrada se ela existir e ainda estiver dentro do TTL."""
        cached: dict[str, Any] | None = self.store.get(key)
        if cached and time.time() - cached["timestamp"] < ttl:
            return cached
        return None

    @staticmethod
    def _normalize(payload: Any) -> dict[str, Any] | None:
        """Normaliza metadados B2C ou formata nomes da divisão de mercado.

        Retorna ``None`` quando o payload não tem um formato de metadados válido.
        Uma cópia profunda evita modificar o objeto recebido do cliente HTTP.
        """
        if not isinstance(payload, dict):
            return None

        root: dict[str, Any] = copy.deepcopy(payload)
        data: Any = root.get("data", root)
        if isinstance(data, dict) and isinstance(data.get("fields"), list):
            fields: list[dict[str, Any]] = []
            for field in data["fields"]:
                if not isinstance(field, dict):
                    continue
                config: Any = field.get("config")
                if not isinstance(config, dict):
                    config = {}
                settings: Any = config.get("settings")
                if not isinstance(settings, dict):
                    settings = {}
                options: Any = (
                    settings.get("options") or settings.get("possible_types") or []
                )
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

        total: Any = root.get("total")
        if (
            isinstance(root.get("recurso"), str)
            and isinstance(root.get("path"), str)
            and isinstance(root.get("aba"), str)
            and isinstance(total, int)
            and not isinstance(total, bool)
            and isinstance(root.get("dados"), list)
        ):
            for item in root["dados"]:
                if isinstance(item, dict) and isinstance(item.get("nome"), str):
                    item["nome"] = capitalizar_nome(item["nome"])
            return root

        return None

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
        cache_ttl: int = CACHE_TTL if ttl is None else ttl
        label: str = baixando or key

        if not resync:
            cached: dict[str, Any] | None = self._get_valid_entry(key, cache_ttl)
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
                cached = self._get_valid_entry(key, cache_ttl)
                if cached:
                    logger.info("AIESEC Cache | HIT pós-lock: '%s'", label)
                    return cached["data"], 200

            action: str = "FORCED RESYNC" if resync else "MISS"
            logger.info("AIESEC Cache | %s: buscando '%s'", action, label)

            try:
                result: Any = fetch()
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

            status: int
            payload: Any
            if (
                isinstance(result, tuple)
                and len(result) == 2
                and isinstance(result[0], int)
            ):
                status, payload = result
            else:
                status, payload = 200, result

            if not 200 <= status < 300:
                log: Callable[..., None] = (
                    logger.error if status >= 500 else logger.warning
                )
                log(
                    "AIESEC Cache | busca de '%s' falhou | HTTP %s %s",
                    label,
                    status,
                    _status_name(status),
                )
                return payload, status

            data: dict[str, Any] | None = self._normalize(payload)
            if data is None:
                payload_keys: list[str] = (
                    sorted(payload.keys()) if isinstance(payload, dict) else []
                )
                is_html: bool = (
                    isinstance(payload, str) and "<html" in payload[:512].lower()
                )
                logger.error(
                    "AIESEC Cache | payload inválido para '%s' | "
                    "tipo=%s chaves=%s html=%s | HTTP %s %s",
                    label,
                    type(payload).__name__,
                    payload_keys,
                    is_html,
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


cache: CacheManager = CacheManager()

__all__ = ["cache", "CacheManager"]
