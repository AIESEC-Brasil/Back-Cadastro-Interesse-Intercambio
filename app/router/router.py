"""Router Module (router.py).

Extensão customizada do APIBlueprint para padronização de rotas e documentação.
Este componente é o que permite a geração automática da documentação Swagger (OpenAPI).
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from collections.abc import Mapping
from functools import wraps
from typing import Any, Callable, Optional
import inspect

from flask_openapi3 import APIBlueprint, OpenAPI
from pydantic import BaseModel


def _serializar_valor(valor: Any) -> Any:
    """Converte modelos Pydantic aninhados em valores aceitos pelo Flask."""
    if isinstance(valor, BaseModel):
        return _serializar_valor(valor.model_dump(mode="json", by_alias=True))
    if isinstance(valor, Mapping):
        return {chave: _serializar_valor(item) for chave, item in valor.items()}
    if isinstance(valor, list):
        return [_serializar_valor(item) for item in valor]
    if isinstance(valor, tuple):
        return tuple(_serializar_valor(item) for item in valor)
    return valor


def _serializar_resposta(resposta: Any) -> Any:
    """Serializa o corpo de resposta, mantendo status e headers de tuplas Flask."""
    if isinstance(resposta, tuple) and resposta:
        return (_serializar_valor(resposta[0]), *resposta[1:])
    return _serializar_valor(resposta)


def _envolver_view_func(view_func: Callable[..., Any]) -> Callable[..., Any]:
    """Serializa o retorno do handler, inclusive quando ele é assíncrono."""
    if inspect.iscoroutinefunction(view_func):
        @wraps(view_func)
        async def async_view(*args: Any, **kwargs: Any) -> Any:
            """Serializa o valor retornado por uma view assíncrona."""
            return _serializar_resposta(await view_func(*args, **kwargs))

        return async_view

    @wraps(view_func)
    def view(*args: Any, **kwargs: Any) -> Any:
        """Serializa o valor retornado por uma view síncrona."""
        return _serializar_resposta(view_func(*args, **kwargs))

    return view


class ApiOpenAPI(OpenAPI):
    """OpenAPI que serializa automaticamente DTOs Pydantic retornados pelas rotas."""

    @staticmethod
    def create_view_func(*args: Any, **kwargs: Any) -> Callable[..., Any]:
        """Envolve cada handler para serializar o resultado após validar a resposta."""
        view_func: Callable[..., Any] = OpenAPI.create_view_func(*args, **kwargs)
        return _envolver_view_func(view_func)


# =================================================================
# 2. CLASSE ROUTER (CUSTOM BLUEPRINT)
# =================================================================

class Router(APIBlueprint):
    """Especialização do APIBlueprint para o ecossistema da aplicação.

    Ao utilizar esta classe, todas as rotas registradas herdarão:
    - Prefixo de URL consistente.
    - Validação automática de schemas de resposta (validate_response=True).
    - Integração direta com a documentação OpenAPI/Swagger.
    """

    def __init__(
            self,
            name: Optional[str] = None,
            url_prefix: str = "",
    ) -> None:
        """Inicializa o Router customizado herdando as funcionalidades do APIBlueprint.

        Args:
            name (Optional[str]): Nome identificador do Blueprint. Se omitido, assume __name__.
            url_prefix (str): Prefixo de URL que antecede todas as rotas registradas neste grupo.
        """
        # Inicializa a classe pai (APIBlueprint)
        # Passamos o nome do blueprint, o nome do módulo atual (__name__)
        # e o prefixo que todas as rotas deste grupo utilizarão.
        super().__init__(
            name or __name__,  # Nome identificador do Blueprint
            __name__,          # Nome do pacote/módulo de importação
            url_prefix=url_prefix,
            # Força a API a validar se o retorno da rota condiz com o DTO/schema documentado
            validate_response=True,
            )

    @staticmethod
    def create_view_func(*args: Any, **kwargs: Any) -> Callable[..., Any]:
        """Cria handlers que validam e serializam automaticamente respostas."""
        view_func: Callable[..., Any] = APIBlueprint.create_view_func(*args, **kwargs)
        return _envolver_view_func(view_func)


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["ApiOpenAPI", "Router"]
