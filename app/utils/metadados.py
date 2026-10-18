"""Acesso seguro aos campos e opções armazenados no cache de metadados B2C."""

from typing import Any, Dict, List, Optional


def buscar_campo_metadado(external_id: str) -> Optional[Dict[str, Any]]:
    """Retorna o campo B2C identificado por ``external_id``, se estiver no cache."""
    from app.cache import cache

    payload: Any = cache.store.get("metadados_b2c", {}).get("data", {})
    if isinstance(payload, list):  # Compatibilidade com cache criado antes da nova estrutura.
        fields: list[Any] = payload
    else:
        data: Any = payload.get("data", payload) if isinstance(payload, dict) else {}
        fields = data.get("fields", []) if isinstance(data, dict) else []

    return next(
        (field for field in fields if isinstance(field, dict) and field.get("external_id") == external_id),
        None,
    )


def buscar_opcoes_metadado(external_id: str) -> List[Dict[str, Any]]:
    """Retorna as opções ativas do campo no formato aninhado do Apps Script."""
    field: Optional[Dict[str, Any]] = buscar_campo_metadado(external_id)
    if not field:
        return []

    config: dict[str, Any] = field.get("config") or {}
    settings: dict[str, Any] = config.get("settings") or {}
    options: list[Any] = (
        settings.get("options") or settings.get("possible_types") or []
    )
    return [
        option for option in options
        if isinstance(option, dict)
        and option.get("status") in ("activate", "active", None)
    ]


__all__ = ["buscar_campo_metadado", "buscar_opcoes_metadado"]
