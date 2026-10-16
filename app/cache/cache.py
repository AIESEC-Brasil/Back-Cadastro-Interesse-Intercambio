"""Cache em memória da resposta fornecida pelo Apps Script B2C."""

import threading
import time
from typing import Any

from ..config import CACHE_TTL


class CacheManager:
    def __init__(self) -> None:
        self.store: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    async def get_or_set(self, key: str, fetch, ttl: int | None = None):
        ttl = CACHE_TTL if ttl is None else ttl
        cached = self.store.get(key)
        if cached and time.time() - cached["timestamp"] < ttl:
            return cached["data"], 200

        with self._lock:
            cached = self.store.get(key)
            if cached and time.time() - cached["timestamp"] < ttl:
                return cached["data"], 200

        status, payload = await fetch()
        if not isinstance(payload, dict) or not 200 <= status < 300:
            return payload, status

        data = payload.get("data", payload)
        fields = data.get("fields", []) if isinstance(data, dict) else []
        active_fields = []
        for item in fields:
            if not isinstance(item, dict):
                continue
            config = item.get("config") or {}
            settings = config.get("settings") or {}
            options = settings.get("options") or settings.get("possible_types") or []
            settings["options"] = [
                option for option in options
                if not isinstance(option, dict)
                or option.get("status") in (None, "activate", "active")
            ]
            config["settings"] = settings
            item["config"] = config
            active_fields.append(item)

        result = {"data": {"fields": active_fields}}
        self.store[key] = {"data": result, "timestamp": time.time()}
        return result, status


cache = CacheManager()
__all__ = ["cache", "CacheManager"]
