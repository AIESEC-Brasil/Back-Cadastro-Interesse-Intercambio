"""Utilitário para normalizar resultados de operações assíncronas e síncronas.

Garante a execução não-bloqueante de corotinas usando await dentro do loop ativo
(evitando o erro RuntimeError: 'This event loop is already running') e realiza o
mapeamento dinâmico de exceções capturadas para DTOs de erro padronizados.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import asyncio  # Biblioteca para verificação de objetos e corotinas assíncronas
import inspect  # Utilitário para inspeção de objetos executáveis e aguardáveis (awaitables)
from typing import Any, Tuple  # Anotações de tipo para retornos e estruturas de dados

from pydantic import ConfigDict  # Configuração de validação para tipos arbitrários no Pydantic

from ..dto import (
    HTTP_EXCEPTION_MAP,
    PYTHON_EXCEPTION_MAP,
    BaseErrorResponse,
    ExceptionErrorResponse,
    HTTPErrorResponse,
    HTTPException,
    PydanticValidationError,
    ValidationErrorResponse,
)


# =================================================================
# 2. NORMALIZADORES DE RESPOSTA E EXCEÇÕES
# =================================================================

@validar
async def resolve_response(result: Any) -> Tuple[int, Any]:
    """Resolve o resultado de uma operação de forma assíncrona e não-bloqueante.

    Garante um retorno uniforme no formato (status_code, body).

    Por que usamos 'async def' com 'await'?
    O uso anterior de 'asyncio.run(result)' tentava criar um novo loop de eventos.
    Se o Flask ou o servidor WSGI/ASGI já tivessem um loop ativo processando
    a requisição, isso causava travamentos ou o erro "event loop is already running".

    Com 'await', reaproveitamos o Event Loop ativo de forma limpa,
    permitindo que o fluxo da aplicação permaneça não-bloqueante.

    Args:
        result (Any): O objeto a ser resolvido. Pode ser um valor direto ou corotina.

    Returns:
        Tuple[int, Any]: Tupla contendo o código de status HTTP (int) e a resposta (Any).
    """
    # Verifica se o objeto retornado é uma corotina ou qualquer outro awaitable
    if asyncio.iscoroutine(result) or inspect.isawaitable(result):
        # Resolve a corotina utilizando o Event Loop ativo
        return await result

    # Se o resultado já for um valor síncrono (dict, string ou tupla), retorna diretamente
    return result


@validar(config=ConfigDict(arbitrary_types_allowed=True))
def resolve_exception(exception: Exception) -> BaseErrorResponse:
    """Mapeia uma exceção capturada para o respectivo DTO de resposta de erro.

    Mantida síncrona por ser uma operação leve de CPU-bound sem I/O.

    Args:
        exception (Exception): Instância da exceção disparada na aplicação.

    Returns:
        BaseErrorResponse: DTO de erro devidamente populado e formatado.
    """
    # Tratamento específico para erros de validação do Pydantic
    if isinstance(exception, PydanticValidationError):
        return ValidationErrorResponse(exception)

    # Tratamento para exceções HTTP conhecidas do Werkzeug / Flask
    if isinstance(exception, HTTPException):
        cls = HTTP_EXCEPTION_MAP.get(type(exception), HTTPErrorResponse)
        return cls(exception)

    # Varre o mapeamento de exceções padrão do Python para encontrar o DTO adequado
    for exc_type, cls in PYTHON_EXCEPTION_MAP.items():
        if isinstance(exception, exc_type):
            return cls(exception)

    # Fallback genérico para exceções não mapeadas explicitamente
    return ExceptionErrorResponse(exception)


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["resolve_response", "resolve_exception"]