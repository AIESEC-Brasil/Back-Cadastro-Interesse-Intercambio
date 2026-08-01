"""Módulo de DTO para Validação de Senha.

Este módulo define a classe utilitária `Senha`, que integra o validador
existente de regras de negócio (`app.utils.validar_senha`) diretamente com
o núcleo de schemas do Pydantic v2 (CoreSchema) para realizar a verificação
de tipo e validação de segurança.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from typing import (
    Any,  # Hint de tipo especial que indica que um valor pode ser de qualquer natureza (dinâmico).
)

from pydantic_core import (
    core_schema,  # Fornece acesso às estruturas de baixo nível do Pydantic para criar validadores customizados complexos.
)


# =================================================================
# 2. TIPO CUSTOMIZADO DE SENHA (CORE SCHEMA)
# =================================================================

class Senha:
    """Classe utilitária avançada para validação e integração de senhas no Pydantic.

    Esta classe não herda de `BaseModel` por design estrutural; ela é configurada para injetar
    comportamentos diretamente no núcleo do Pydantic v2 (`CoreSchema`), agindo como um tipo de dado primitivo
    customizado que retorna uma `str` pura após passar pelas travas de segurança do projeto.
    """

    @classmethod
    def __get_pydantic_core_schema__(
            cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        """Injeta a lógica de pré-validação customizada da classe dentro do fluxo de tipagem do Pydantic v2.

        Associa a função estática `cls.validar` para rodar imediatamente antes do interpretador consolidar
        a estrutura final baseada no esquema nativo de string (`str_schema`).

        Args:
            _source_type (Any): O tipo de origem que está sendo avaliado pelo Pydantic.
            _handler (Any): Manipulador do esquema pai da cadeia de validação.

        Returns:
            core_schema.CoreSchema: Esquema interno configurado com a função validadora da classe.
        """
        return core_schema.no_info_before_validator_function(
            cls.validar,
            core_schema.str_schema(),
        )

    @staticmethod
    def validar(value: Any) ->  str:
        """Executa a verificação prévia de tipo e delega a validação para o utilitário central do projeto.

        Garante que o dado recebido seja estritamente uma string antes de passá-lo para
        o módulo utilitário `validar_senha`, evitando exceções inesperadas em tempo de execução.

        Args:
            value (Any): O valor bruto de senha oriundo da requisição ou do banco.

        Returns:
            str: String contendo a senha após validação com sucesso.

        Raises:
            ValueError: Se a entrada não for do tipo string ou se o utilitário reprovar
                        os critérios de segurança da senha.
        """
        from app.utils import (
            validar_senha,  # Função utilitária centralizada responsável por aplicar as regras de complexidade de senha.
        )
        # Trava de segurança: valida se a entrada recebida é de fato um tipo textual
        if not isinstance(value, str):
            raise ValueError("Tipo de dado inválido para senha. Deve ser uma string.")

        # Delega o fluxo de verificação de regras para o utilitário do projeto e retorna a string
        return validar_senha(value)


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["Senha"]