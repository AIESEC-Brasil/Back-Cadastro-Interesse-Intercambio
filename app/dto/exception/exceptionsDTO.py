"""
Módulo de respostas padronizadas de erro para APIs.

Contém:
- Classe base para erros
- Tratamento de ValidationError do Pydantic
- Tratamento genérico de Exception
- Mapeamento automático de exceções HTTP do Werkzeug
- Diversas exceções padrão do Python

Padrão:
Todas as classes possuem apenas __init__ como método.
O nome do tipo do erro é capturado automaticamente quando aplicável.
"""

# BaseModel → usado para criar modelos de resposta estruturados
# Field → permite configurar valores padrão corretamente (ex: listas mutáveis)
# ValidationError → exceção lançada pelo Pydantic quando há erro de validação
from pydantic import BaseModel, Field, ValidationError as PydanticValidationError, ConfigDict

# List → tipagem para lista de strings
from typing import List,Type,Dict,Any

# HTTPException → exceções HTTP padrão usadas em frameworks como Flask
from werkzeug.exceptions import HTTPException

from deep_translator import GoogleTranslator

# class personalizada para enum do httpstatus
from ..output import HttpStatus



# ==========================================================
# BASE ERROR
# ==========================================================

class BaseErrorResponse(BaseModel):
    """
    Classe base para todas as respostas de erro da aplicação.

    Attributes:
        error (bool): Sempre True para indicar erro.
        type (str): Tipo do erro (ex: ValueError, NotFound, etc).
        message (str): Mensagem descritiva do erro.
        error_details (List[str]): Lista opcional de detalhes adicionais.
        status_code (HttpStatus): Código HTTP associado ao erro (se aplicável).
    """
    # Isso força o Pydantic a validar e REJEITAR campos extras
    model_config = ConfigDict(extra='forbid')
    error: bool = True
    type: str
    message: str
    error_details: List[Dict[str,Any]] = Field(default_factory=list)
    status_code: HttpStatus = HttpStatus.INTERNAL_SERVER_ERROR


# ==========================================================
# VALIDAÇÃO PYDANTIC
# ==========================================================

class ValidationErrorResponse(BaseErrorResponse):
    """
    Resposta específica para erros de validação do Pydantic.

    Extrai automaticamente todas as mensagens de erro
    retornadas pelo ValidationError.
    """

    def __init__(self, exception: PydanticValidationError = None, **kwargs):
        # Se vier uma exceção, extraímos os dados dela e alimentamos o dicionário de inicialização
        if exception is not None:
            # No seu resolve_exception
            error_details = []
            erros_processados = set()  # Onde faremos o "pulo" inteligente

            for erro in exception.errors():
                # 1. Gera o rastro visual: "comite -> id" ou "comite -> nome"
                rastro = " -> ".join([str(item) for item in erro["loc"]])

                msg_original = erro['msg']

                # 2. A CHAVE ÚNICA: combina o rastro com a mensagem original
                # Isso garante que:
                # - comite -> id (erro A) apareça
                # - comite -> nome (erro B) apareça
                # - comite -> id (erro A repetido) SEJA PULADO
                chave_unica = f"{rastro}|{msg_original}"

                if chave_unica not in erros_processados:
                    # 3. Traduz apenas o que é novo
                    msg_pt = GoogleTranslator(source='auto', target='pt').translate(msg_original)

                    # 4. Adiciona à lista de detalhes
                    error_details.append({
                        "loc": rastro,
                        "msg": msg_pt
                    })

                    # Marca como processado para não repetir se aparecer de novo
                    erros_processados.add(chave_unica)

            kwargs.update({
                "type": "ValidationError",
                "message": "Dados inválidos",
                "error_details": error_details,
                "status_code": HttpStatus.UNPROCESSABLE_ENTITY
            })
        # Chama o construtor do Pydantic (BaseModel) com os campos processados
        super().__init__(**kwargs)


# ==========================================================
# EXCEPTION GENÉRICA
# ==========================================================

class ExceptionErrorResponse(BaseErrorResponse):
    """
    Resposta genérica para qualquer exceção.

    Captura automaticamente:
    - Nome real da exceção
    - Mensagem original do erro
    """
    def __init__(self, exception: Exception=None,**kwargs):
        if exception is not None:
            kwargs.update({
                "type":exception.__class__.__name__,
                "message":str(exception),
                "error_details":[],
                "status_code":HttpStatus.INTERNAL_SERVER_ERROR
            })
        super().__init__(**kwargs)

# ==========================================================
# EXCEÇÕES PYTHON COMUNS
# ==========================================================

class ValueErrorResponse(ExceptionErrorResponse):
    """Erro para ValueError."""
    pass
class TypeErrorResponse(ExceptionErrorResponse):
    """Erro para TypeError."""
    pass
class IndexErrorResponse(ExceptionErrorResponse):
    """Erro para IndexError."""
    pass
class KeyErrorResponse(ExceptionErrorResponse):
    """Erro para KeyError."""
    pass
class AttributeErrorResponse(ExceptionErrorResponse):
    """Erro para AttributeError."""
    pass
class RuntimeErrorResponse(ExceptionErrorResponse):
    """Erro para RuntimeError."""
    pass
class ZeroDivisionErrorResponse(ExceptionErrorResponse):
    """Erro para ZeroDivisionError."""
    pass
class PermissionErrorResponse(ExceptionErrorResponse):
    """Erro para PermissionError."""
    pass
class FileNotFoundErrorResponse(ExceptionErrorResponse):
    """Erro para FileNotFoundError."""
    pass
class TimeoutErrorResponse(ExceptionErrorResponse):
    """Erro para TimeoutError."""
    pass
class NotImplementedErrorResponse(ExceptionErrorResponse):
    """Erro para NotImplementedError."""
    pass


# ==========================================================
# EXCEÇÕES HTTP (WERKZEUG)
# ==========================================================

class HTTPErrorResponse(BaseErrorResponse):
    """
    Resposta para exceções HTTP do Werkzeug.

    Captura automaticamente:
    - Nome da exceção (BadRequest, NotFound, etc)
    - Descrição padrão do erro
    - status_code convertido para HttpStatus
    """
    def __init__(self, exception: HTTPException):
        code = getattr(exception, "code", None)
        status_code = HttpStatus(code) if code in HttpStatus._value2member_map_ else HttpStatus.INTERNAL_SERVER_ERROR
        super().__init__(
            type=exception.__class__.__name__,
            message=exception.description,
            error_details=[],
            status_code=status_code
        )


# Classes HTTP específicas
class BadRequestResponse(HTTPErrorResponse):
    """Erro HTTP 400 - Bad Request."""
    pass
class UnauthorizedResponse(HTTPErrorResponse):
    """Erro HTTP 401 - Unauthorized."""
    pass
class ForbiddenResponse(HTTPErrorResponse):
    """Erro HTTP 403 - Forbidden."""
    pass
class NotFoundResponse(HTTPErrorResponse):
    """Erro HTTP 404 - Not Found."""
    pass
class MethodNotAllowedResponse(HTTPErrorResponse):
    """Erro HTTP 405 - Method Not Allowed."""
    pass
class ConflictResponse(HTTPErrorResponse):
    """Erro HTTP 409 - Conflict."""
    pass
class UnprocessableEntityResponse(HTTPErrorResponse):
    """Erro HTTP 422 - Unprocessable Entity."""
    pass
class TooManyRequestsResponse(HTTPErrorResponse):
    """Erro HTTP 429 - Too Many Requests."""
    pass
class InternalServerErrorResponse(HTTPErrorResponse):
    """Erro HTTP 500 - Internal Server Error."""
    pass
class BadGatewayResponse(HTTPErrorResponse):
    """Erro HTTP 502 - Bad Gateway."""
    pass
class ServiceUnavailableResponse(HTTPErrorResponse):
    """Erro HTTP 503 - Service Unavailable."""
    pass
class GatewayTimeoutResponse(HTTPErrorResponse):
    """Erro HTTP 504 - Gateway Timeout."""
    pass

# ==========================================================
# MAPEAMENTO AUTOMÁTICO DE EXCEÇÕES
# ==========================================================

# Mapear exceções Python para classes específicas
PYTHON_EXCEPTION_MAP: Dict[Type[Exception], Type[ExceptionErrorResponse]] = {
    ValueError: ValueErrorResponse,
    TypeError: TypeErrorResponse,
    IndexError: IndexErrorResponse,
    KeyError: KeyErrorResponse,
    AttributeError: AttributeErrorResponse,
    RuntimeError: RuntimeErrorResponse,
    ZeroDivisionError: ZeroDivisionErrorResponse,
    PermissionError: PermissionErrorResponse,
    FileNotFoundError: FileNotFoundErrorResponse,
    TimeoutError: TimeoutErrorResponse,
    NotImplementedError: NotImplementedErrorResponse,
}

# Mapear exceções HTTP para classes específicas
HTTP_EXCEPTION_MAP: Dict[Type[HTTPException], Type[HTTPErrorResponse]] = {
    HTTPException: HTTPErrorResponse,  # genérico, qualquer HTTPException
    # opcional: você pode mapear explicitamente BadRequest, NotFound etc. se quiser
}

# ==========================================================
# __all__
# ==========================================================

__all__ = [
    "BaseErrorResponse",
    "ValidationErrorResponse",
    "ExceptionErrorResponse",
    "HTTPErrorResponse",
    "BadRequestResponse",
    "UnauthorizedResponse",
    "ForbiddenResponse",
    "NotFoundResponse",
    "MethodNotAllowedResponse",
    "ConflictResponse",
    "UnprocessableEntityResponse",
    "TooManyRequestsResponse",
    "InternalServerErrorResponse",
    "BadGatewayResponse",
    "ServiceUnavailableResponse",
    "GatewayTimeoutResponse",
    "HTTPException",
    "PydanticValidationError",
    "PYTHON_EXCEPTION_MAP",
    "HTTP_EXCEPTION_MAP"
]