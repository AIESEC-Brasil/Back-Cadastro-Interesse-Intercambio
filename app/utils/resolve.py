"""
Utilitário para normalizar resultados de operações assíncronas/síncronas.

resolve_response executa corotinas (awaitables) imediatamente com asyncio.run
quando necessário, retornando sempre uma tupla consistente (status, data).
"""

# ==============================
# Importações (Dependencies)
# ==============================
import asyncio  # Biblioteca para gerenciamento de programação assíncrona e loops de eventos
from pydantic import ConfigDict
from typing import Any, Tuple  # Suporte para anotações de tipo genéricas e estruturas de tuplas
from ..dto import PYTHON_EXCEPTION_MAP,HTTP_EXCEPTION_MAP,BaseErrorResponse,ValidationErrorResponse,HTTPErrorResponse,\
PydanticValidationError,HTTPException,ExceptionErrorResponse

# ==============================
# Normalizador de Resposta
# ==============================

@validar
def resolve_response(result: Any) -> Tuple[int, Any]:
    """
    Resolve o resultado de uma operação, garantindo um retorno uniforme de (status, data).

    Esta função identifica se o resultado passado é uma corotina (objeto awaitable).
    Se for, ela bloqueia a execução atual para rodar a corotina até o fim usando
    um event loop temporário. Se for um valor comum, apenas o repassa.



    Args:
        result (Any): O objeto a ser resolvido. Pode ser um valor direto ou uma corotina pendente.

    Returns:
        Tuple[int, Any]: Uma tupla contendo o código de status HTTP (int) e o corpo da resposta (Any).
    """

    # Verifica se o objeto retornado é uma corotina (criada por uma função 'async def')
    if asyncio.iscoroutine(result):
        # Inicia um loop de eventos interno, executa a tarefa e retorna o resultado final
        return asyncio.run(result)

    # Se o resultado já for um valor síncrono, retorna-o diretamente
    return result

@validar(config=ConfigDict(arbitrary_types_allowed=True))
def resolve_exception(exception: Exception) -> BaseErrorResponse:
    """
    Retorna a instância correta da Response com status_code.
    """
    if isinstance(exception, PydanticValidationError):
        return ValidationErrorResponse(exception)

    if isinstance(exception, HTTPException):
        cls = HTTP_EXCEPTION_MAP.get(type(exception), HTTPErrorResponse)
        return cls(exception)

    for exc_type, cls in PYTHON_EXCEPTION_MAP.items():
        if isinstance(exception, exc_type):
            return cls(exception)

    return ExceptionErrorResponse(exception)

# ==============================
# Exportações
# ==============================
__all__ = ["resolve_response","resolve_exception"]