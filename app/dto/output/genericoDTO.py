"""Módulo para padronização e encapsulamento genérico de respostas de API."""

from typing import (
    Any,       # Type hint para valores dinâmicos/não especificados
    Dict,      # Type hint para estruturas de dicionário
    Generic,   # Classe base para suporte a generics parametrizáveis
    List,      # Type hint para coleções de listas
    Optional,  # Type hint para campos que aceitam o tipo informado ou None
    Type,      # Type hint para referências a classes/tipos
    TypeVar,   # Construtor de variáveis de tipo para classes genéricas
)

from deep_translator import GoogleTranslator  # Utilitário para tradução de mensagens de validação
from pydantic import (
    BaseModel,    # Classe base do Pydantic para schemas e DTOs
    ConfigDict,   # Objeto de configuração do comportamento dos modelos Pydantic
    Field,        # Função para definição de validações e metadados de atributos
)

# Variável de tipo genérica parametrizável para o atributo 'data'
T = TypeVar("T")


class RetornoGenerico(BaseModel, Generic[T]):
    """Envelope genérico para padronização de respostas de erro ou sucesso da API.

    Esta classe utiliza *Generics* do Python e Pydantic para permitir que o campo
    `data` receba qualquer tipo de estrutura (como `dict`, `str`, `list` ou outro
    DTO do Pydantic), garantindo a validação e o suporte à documentação OpenAPI.

    Attributes:
        sucesso (bool): Indicador do status do processamento da requisição. Padrão é `True`.
        data (Optional[T]): Payload dinâmico contendo dados de sucesso ou detalhes do erro.
            Padrão é `None`.

    Example:
        >>> # Uso com Dicionário
        >>> resposta = RetornoGenerico[dict](
        ...     sucesso=False,
        ...     data={"campo": "email", "mensagem": "Formato inválido"}
        ... )
        >>> print(resposta.model_dump())
        {'sucesso': False, 'data': {'campo': 'email', 'mensagem': 'Formato inválido'}}

        >>> # Registro em rotas do Flask-OpenAPI3 / FastAPI
        >>> @api.post("/exemplo", responses={400: RetornoGenerico[dict]})
        ... def minha_rota():
        ...     pass
    """

    # Configuração global: descarta quaisquer atributos extras não definidos no modelo
    model_config = ConfigDict(extra="ignore")

    sucesso: bool = Field(
        default=True,
        description="Indica se a requisição foi processada com sucesso."
    )
    data: Optional[T] = Field(
        default=None,
        description="Payload genérico contendo dados complementares ou detalhes do erro."
    )


__all__ = ["RetornoGenerico"]