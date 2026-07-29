"""
Utilitário para normalizar resultados de operações assíncronas/síncronas de forma não-bloqueante.

resolve_response executa corotinas (awaitables) usando await dentro do loop ativo,
garantindo compatibilidade com ambientes assíncronos e evitando o erro:
"RuntimeError: This event loop is already running".
"""

# ==============================
# Importações (Dependencies)
# ==============================
import asyncio  # Biblioteca para verificação de objetos assíncronos (corotinas)
import inspect

from pydantic import ConfigDict
from typing import Any, Tuple  # Suporte para anotações de tipo genéricas e estruturas de tuplas
from ..dto import (
    PYTHON_EXCEPTION_MAP,
    HTTP_EXCEPTION_MAP,
    BaseErrorResponse,
    ValidationErrorResponse,
    HTTPErrorResponse,
    PydanticValidationError,
    HTTPException,
    ExceptionErrorResponse
)

# ==============================
# Normalizador de Resposta
# ==============================

@validar
async def resolve_response(result: Any) -> Tuple[int, Any]:
    """
    Resolve o resultado de uma operação de forma assíncrona e não-bloqueante,
    garantindo um retorno uniforme de (status, data).

    Por que mudamos para 'async def' com 'await'?
    O uso anterior de 'asyncio.run(result)' tentava abrir um novo loop de eventos.
    Se o Flask ou o middleware já tivessem um loop ativo processando a request,
    isso causava um travamento ou erro de "event loop is already running".

    Usando 'await', nós pegamos "carona" no loop que já está rodando de forma limpa,
    permitindo que todo o fluxo da aplicação permaneça assíncrono de ponta a ponta.

    Args:
        result (Any): O objeto a ser resolvido. Pode ser um valor direto ou uma corotina pendente.

    Returns:
        Tuple[int, Any]: Uma tupla contendo o código de status HTTP (int) e o corpo da resposta (Any).
    """

    # Verifica se o objeto retornado é uma corotina (criada por uma função 'async def')
    # ou qualquer outro objeto aguardável (awaitable)
    if asyncio.iscoroutine(result) or inspect.isawaitable(result):
        # Resolve a corotina usando o Event Loop ativo sem criar loops novos e concorrentes
        return await result

    # Se o resultado já for um valor síncrono (um dict, string ou tupla já resolvida), retorna-o diretamente
    return result


@validar(config=ConfigDict(arbitrary_types_allowed=True))
def resolve_exception(exception: Exception) -> BaseErrorResponse:
    """
    Retorna a instância correta da classe de Response de erro com base na exceção capturada.
    Mantida síncrona, pois o tratamento de exceções em si é uma operação CPU-bound simples e rápida.
    """
    # Tratamento específico para erros de validação de esquemas Pydantic
    if isinstance(exception, PydanticValidationError):
        return ValidationErrorResponse(exception)

    # Tratamento para exceções HTTP conhecidas do sistema
    if isinstance(exception, HTTPException):
        cls = HTTP_EXCEPTION_MAP.get(type(exception), HTTPErrorResponse)
        return cls(exception)

    # Varre o mapa de exceções padrão do Python para envelopar o erro no DTO correto
    for exc_type, cls in PYTHON_EXCEPTION_MAP.items():
        if isinstance(exception, exc_type):
            return cls(exception)

    # Fallback genérico para qualquer erro inesperado do sistema (Ex: KeyError, ValueError não mapeados)
    return ExceptionErrorResponse(exception)


# ==============================
# Exportações
# ==============================
__all__ = ["resolve_response", "resolve_exception"]