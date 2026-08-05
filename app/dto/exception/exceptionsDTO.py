"""Módulo de respostas padronizadas de erro para APIs.

Contém:
- Classe base para erros (`BaseErrorResponse`)
- Tratamento de `ValidationError` do Pydantic (`ValidationErrorResponse`)
- Tratamento genérico de `Exception` (`ExceptionErrorResponse`)
- Mapeamento automático de exceções HTTP do Werkzeug (`HTTPErrorResponse`)
- Diversas exceções padrão do Python e dicionários de mapeamento dinâmico.

Padrão:
Todas as classes derivam de BaseModel e padronizam a resposta da API em JSON.
O nome do tipo do erro é capturado automaticamente quando aplicável.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import ast #módulo que permite ao Python "entender", analisar e manipular a estrutura do próprio código Python antes de executá-lo
from typing import (
    Any,   # Hint para tipos genéricos/dinâmicos
    Dict,  # Hint de tipo para dicionários
    List,  # Hint de tipo para coleções do tipo lista
    Type,  # Hint de tipo para referências de classes/tipos
    Generic,   # Classe base para criação de modelos e DTOs genéricos parametrizáveis
    TypeVar,   # Construtor de variáveis de tipo utilizadas em classes Generics
    Optional,  # Type hint para indicar que o atributo aceita o tipo informado ou None
)
from deep_translator import GoogleTranslator  # Biblioteca de tradução para converter mensagens de erro do Pydantic
from pydantic import (
    BaseModel,                               # Classe base do Pydantic para validação e estruturação de modelos
    ConfigDict,                              # Objeto de configuração para comportamentos do modelo (ex: extra='forbid')
    Field,                                   # Função para configurar metadados e valores padrão de atributos
    ValidationError as PydanticValidationError,  # Alias para a exceção nativa de validação do Pydantic
)
from werkzeug.exceptions import HTTPException  # Exceções HTTP nativas do ecossistema Werkzeug/Flask

from ..output import HttpStatus  # Importa o enumerador customizado de códigos HTTP da aplicação

# Definição do TypeVar para permitir qualquer tipo genérico no parâmetro 'dados'
T = TypeVar('T')

# =================================================================
# 2. BASE ERROR MODEL
# =================================================================

class BaseErrorResponse(BaseModel):
    """Classe base para todas as respostas de erro da aplicação.

    Attributes:
        error (bool): Sempre True para indicar estado de erro.
        type (str): Tipo/Nome da exceção (ex: ValueError, NotFound, etc).
        message (str): Mensagem descritiva legível do erro.
        error_details (List[Dict[str, Any]]): Lista com os detalhes e localização dos erros.
        status_code (HttpStatus): Código HTTP associado à resposta de erro.
    """

    # Força o Pydantic a validar e REJEITAR campos extras não declarados
    model_config = ConfigDict(extra="forbid")

    # Flag booleana indicando a presença de falha na operação
    error: bool = True

    # Nome da classe da exceção ou categoria do erro
    type: str

    # Descrição geral ou resumida do erro retornado
    message: str

    # Lista estruturada contendo o rastro detalhado das falhas (ex: local e mensagem)
    error_details: List[Dict[str, Any]] = Field(default_factory=list)

    # Código de status HTTP associado à resposta da API
    status_code: HttpStatus = HttpStatus.INTERNAL_SERVER_ERROR

class AppError(Exception):
    """Exceção customizada da aplicação para disparo direto via `raise`.

    Encapsula as informações de falha em uma instância do DTO `BaseErrorResponse`,
    permitindo que exceções de regras de negócio ou validação sejam lançadas em
    uma única linha e posteriormente interceptadas e tratadas de forma padronizada.

    Attributes:
        dto (BaseErrorResponse): Instância do DTO de resposta de erro contendo
            os detalhes formatados e prontos para serialização JSON na API.

    Args:
        type (str): Nome ou categoria do erro (ex: `"ValidationError"`, `"NotFoundError"`).
        message (str): Descrição geral ou mensagem principal legível do erro.
        status_code (HttpStatus, optional): Código de status HTTP associado à falha.
            Defaults to `HttpStatus.UNPROCESSABLE_ENTITY`.
        error_details (List[Dict[str, Any]] | None, optional): Lista contendo o rastro
            detalhado e a localização dos erros (ex: `[{"loc": "senha", "msg": "..."}]`).
            Defaults to `None` (inicializado internamente como lista vazia).

    Example:
        >>> raise AppError(
        ...     type="ValidationError",
        ...     message="Dados inválidos",
        ...     status_code=HttpStatus.UNPROCESSABLE_ENTITY,
        ...     error_details=[{"loc": "senha", "msg": "A senha deve ter no mínimo 8 caracteres."}]
        ... )
    """

    def __init__(
            self,
            type: str,
            message: str,
            status_code: HttpStatus = HttpStatus.UNPROCESSABLE_ENTITY,
            error_details: List[Dict[str, Any]] | None = None,
    ) -> None:
        # Instancia o DTO de erro com os dados fornecidos
        self.dto = BaseErrorResponse(
            type=type,
            message=message,
            status_code=status_code,
            error_details=error_details or [],
        )
        # Repassa a mensagem principal para o construtor nativo de Exception
        super().__init__(message)

# =================================================================
# 3. VALIDAÇÃO PYDANTIC
# =================================================================

class ValidationErrorResponse(BaseErrorResponse):
    """Resposta específica para erros de validação do Pydantic.

    Extrai automaticamente todas as mensagens de erro retornadas pelo
    PydanticValidationError, traduzindo-as para português e evitando duplicidades.
    """

    def __init__(self, exception: PydanticValidationError = None, **kwargs: Any) -> None:
        """Inicializa o modelo de erro extraindo os detalhes do ValidationError.

        Args:
            exception (PydanticValidationError, optional): Exceção de validação capturada.
            **kwargs: Atributos adicionais passados para o construtor do BaseModel.
        """
        # Se vier uma exceção, extraímos os dados dela e alimentamos o dicionário de inicialização
        if exception is not None:
            error_details: List[Dict[str, Any]] = []
            erros_processados = set()  # Conjunto para garantir que erros idênticos no mesmo campo não repitam

            for erro in exception.errors():
                # 1. Gera o rastro visual da localização: "comite -> id" ou "comite -> nome"
                rastro = " -> ".join([str(item) for item in erro["loc"]])

                msg_original = erro["msg"]

                # 2. CHAVE ÚNICA: combina o rastro com a mensagem original
                # Isso garante que falhas em campos diferentes apareçam, mas duplicações idênticas sejam ignoradas
                chave_unica = f"{rastro}|{msg_original}"

                if chave_unica not in erros_processados:
                    # 3. Traduz apenas as mensagens inéditas via GoogleTranslator
                    msg_pt = GoogleTranslator(source="auto", target="pt").translate(msg_original)

                    # 4. Adiciona à lista de detalhes no formato padronizado da API
                    dado = msg_pt.replace("Value error, ", "", 1)
                    error_details.append({
                        "loc": rastro,
                        "msg": ast.literal_eval(dado) if isinstance(dado, str) and dado.startswith("[") else dado,
                    })

                    # Marca como processado no set para controle de duplicidade
                    erros_processados.add(chave_unica)

            # Atualiza os kwargs com as propriedades específicas do erro de validação
            kwargs.update({
                "type": "ValidationError",
                "message": "Dados inválidos",
                "error_details": error_details,
                "status_code": HttpStatus.UNPROCESSABLE_ENTITY,
            })

        # Chama o construtor da classe pai (BaseErrorResponse / BaseModel)
        super().__init__(**kwargs)


# =================================================================
# 4. EXCEPTION GENÉRICA E NATIVA DO PYTHON
# =================================================================

class ExceptionErrorResponse(BaseErrorResponse):
    """Resposta genérica para qualquer exceção não tratada especificamente.

    Captura automaticamente:
    - Nome real da classe da exceção
    - Mensagem original emitida pelo interpretador Python
    """

    def __init__(self, exception: Exception = None, **kwargs: Any) -> None:
        """Inicializa a resposta com base na exceção genérica capturada.

        Args:
            exception (Exception, optional): Instância da exceção genérica.
            **kwargs: Parâmetros sobrescritos para o construtor base.
        """
        if exception is not None:
            kwargs.update({
                "type": exception.__class__.__name__,
                "message": str(exception),
                "error_details": [],
                "status_code": HttpStatus.INTERNAL_SERVER_ERROR,
            })
        super().__init__(**kwargs)

class ErroGenerico(BaseModel, Generic[T]):
    """Envelope genérico para padronização de estruturas de resposta ou erro na API.

    Esta classe utiliza *Generics* do Python e Pydantic para permitir que o campo
    `dados` receba qualquer tipo de estrutura (como `dict`, `str`, `list` ou outro
    DTO do Pydantic), mantendo a validação e a geração de schemas no Swagger/OpenAPI.

    Attributes:
        sucesso (bool): Indicador booleano do status da operação. Padrão é `True`.
        dados (Optional[T]): Conteúdo flexível contendo os dados do payload ou
            detalhes do erro. Padrão é `None`.

    Example:
        >>> # Uso com Dicionário (dict)
        >>> resposta_dict = ErroGenerico[dict](
        ...     sucesso=False,
        ...     dados={"campo": "email", "mensagem": "Formato inválido"}
        ... )
        >>> print(resposta_dict.model_dump())
        {'sucesso': False, 'dados': {'campo': 'email', 'mensagem': 'Formato inválido'}}

        >>> # Uso no flask-openapi3 (Responses da Rota)
        >>> @api.post("/exemplo", responses={400: ErroGenerico[dict]})
        ... def minha_rota():
        ...     pass
    """

    sucesso: bool = Field(
        default=True,
        description="Indica se a requisição foi processada com sucesso."
    )
    dados: Optional[T] = Field(
        default=None,
        description="Payload genérico contendo dados complementares ou detalhes do erro."
    )


# Subclasses de exceções nativas do Python para mapeamento dinâmico
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


# =================================================================
# 5. EXCEÇÕES HTTP (WERKZEUG / FLASK)
# =================================================================

class HTTPErrorResponse(BaseErrorResponse):
    """Resposta para exceções HTTP do Werkzeug.

    Captura automaticamente:
    - Nome da exceção (ex: BadRequest, NotFound, etc)
    - Descrição padrão do erro emitida pelo Werkzeug
    - status_code convertido para o enum HttpStatus da aplicação
    """

    def __init__(self, exception: HTTPException) -> None:
        """Inicializa a resposta a partir de uma HTTPException.

        Args:
            exception (HTTPException): Exceção do Werkzeug capturada no manipulador da aplicação.
        """
        code = getattr(exception, "code", None)
        status_code = (
            HttpStatus(code)
            if code in HttpStatus._value2member_map_
            else HttpStatus.INTERNAL_SERVER_ERROR
        )
        super().__init__(
            type=exception.__class__.__name__,
            message=exception.description,
            error_details=[],
            status_code=status_code,
        )


# Subclasses HTTP específicas para retornos direcionados
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


# =================================================================
# 6. MAPEAMENTO AUTOMÁTICO DE EXCEÇÕES
# =================================================================

# Mapeia tipos de exceções Python padrão para suas respectivas classes DTO de erro
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

# Mapeia exceções HTTP genéricas do Werkzeug para a classe base de erro HTTP
HTTP_EXCEPTION_MAP: Dict[Type[HTTPException], Type[HTTPErrorResponse]] = {
    HTTPException: HTTPErrorResponse,  # Genérico para capturar qualquer sub-exceção HTTP Werkzeug
}


# =================================================================
# 7. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = [
    "AppError",
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
    "HTTP_EXCEPTION_MAP",
    "ErroGenerico",
]