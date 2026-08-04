"""Módulo de DTO para Validação de Tag.

Este módulo define a classe utilitária `Tag`, que integra a validação estrita de
tags (sem espaços, sem acentos e em letras minúsculas) diretamente com o núcleo
de schemas do Pydantic v2 (CoreSchema).
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import unicodedata  # Módulo nativo para análise e detecção de caracteres Unicode/acentos.
from typing import (
    Any,  # Hint de tipo especial que indica que um valor pode ser de qualquer natureza (dinâmico).
)

from pydantic_core import (
    core_schema,  # Fornece acesso às estruturas de baixo nível do Pydantic para criar validadores customizados complexos.
)


# =================================================================
# 2. TIPO CUSTOMIZADO DE TAG (CORE SCHEMA)
# =================================================================

class Tag:
    """Classe utilitária para validação estrita de tags no Pydantic v2.

    Esta classe não herda de `BaseModel` por design estrutural; ela é configurada para injetar
    comportamentos diretamente no núcleo do Pydantic v2 (`CoreSchema`), agindo como um tipo de dado primitivo
    customizado que retorna uma `str` pura após passar pelas travas de validação.
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
    def validar(value: Any) -> str:
        """Executa a verificação estrita do formato da tag.

        Garante que o dado recebido seja uma string válida, totalmente em letras minúsculas,
        sem espaços e sem nenhum caractere acentuado.

        Args:
            value (Any): O valor bruto da tag oriundo da requisição ou do banco.

        Returns:
            str: String contendo a tag validada.

        Raises:
            ValueError: Se a entrada não for string, ou se contiver espaços, acentos ou maiúsculas.
        """
        # Trava de segurança: valida se a entrada recebida é de fato um tipo textual
        if not isinstance(value, str):
            raise ValueError("Dados Inválidos: Tipo de dado inválido para tag. Deve ser uma string.")

        # Validação de espaços
        if " " in value:
            raise ValueError("Dados Inválidos: A tag não pode conter espaços.")

        # Validação de caixa baixa (não permite maiúsculas)
        if value != value.lower():
            raise ValueError("Dados Inválidos: A tag deve conter apenas letras minúsculas.")

        # Validação de acentos e diacríticos
        texto_decomposto = unicodedata.normalize("NFD", value)
        tem_acento = any(unicodedata.category(c) == "Mn" for c in texto_decomposto)

        if tem_acento:
            raise ValueError("Dados Inválidos: A tag não pode conter acentos ou caracteres especiais.")

        return value


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["Tag"]