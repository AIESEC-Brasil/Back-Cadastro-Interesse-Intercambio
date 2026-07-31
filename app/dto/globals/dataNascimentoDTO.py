"""Módulo de DTO para Validação de Data de Nascimento.

Este módulo define a classe utilitária `DataNascimento`, que integra diretamente
com o núcleo de schemas do Pydantic v2 (CoreSchema) para realizar a normalização,
parse e validação de consistência cronológica de datas de nascimento.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from datetime import (
    date,      # Objeto padrão para manipulação de datas calendárias (dia, mês, ano).
    datetime,  # Objeto padrão para manipulação de carimbos de data e hora (timestamp).
)
from typing import (
    Any,  # Hint de tipo especial que indica que um valor pode ser de qualquer natureza (dinâmico).
)

from pydantic_core import (
    core_schema,  # Fornece acesso às estruturas de baixo nível do Pydantic para criar validadores customizados complexos.
)


# =================================================================
# 2. TIPO CUSTOMIZADO DE DATA DE NASCIMENTO (CORE SCHEMA)
# =================================================================

class DataNascimento:
    """Classe utilitária avançada para validação, normalização e parsing de datas de nascimento.

    Esta classe não herda de `BaseModel` por design estrutural; ela é configurada para injetar
    comportamentos diretamente no núcleo do Pydantic v2 (`CoreSchema`), agindo como um tipo de dado primitivo
    customizado que retorna uma instância pura de `datetime`, eliminando chaves aninhadas desnecessárias no JSON final.
    """

    @classmethod
    def __get_pydantic_core_schema__(
            cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        """Injeta a lógica de pré-validação customizada da classe dentro do fluxo de tipagem do Pydantic v2.

        Associa a função estática `cls.validar` para rodar imediatamente antes do interpretador consolidar
        a estrutura final baseada no esquema nativo de data e hora (`datetime_schema`).
        """
        return core_schema.no_info_before_validator_function(
            cls.validar,
            core_schema.datetime_schema(),
        )

    @staticmethod
    def validar(value: Any) -> datetime:
        """Executa a normalização cronológica de strings temporais, impedindo inclusive registros em datas futuras.

        Suporta múltiplos formatos de entrada de mercado, incluindo strings de data pura (YYYY-MM-DD),
        data e hora completas, e strings contendo marcação de fuso horário ISO 8601 (suportando o caractere de sufixo Z).

        Args:
            value (Any): O valor de data bruto oriundo da requisição ou do banco.

        Returns:
            datetime: Objeto padrão datetime nativo do Python após o parse com sucesso.

        Raises:
            ValueError: Se a string não casar com nenhum formato temporal suportado ou se a data for futura.
        """
        nascimento = value

        # Se a entrada recebida for uma string textual, inicia o ciclo de conversões experimentais
        if isinstance(value, str):
            # Varre os formatos tradicionais de tempo usados na comunicação interna da aplicação
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    nascimento = datetime.strptime(value, fmt)
                    break  # Converteu com sucesso: interrompe o laço de tentativas imediatamente
                except ValueError:
                    continue  # Falhou no formato atual: testa o próximo item do array

            # Caso os formatos tradicionais falhem, processa o dado usando as especificações da ISO 8601
            if isinstance(nascimento, str):
                try:
                    # Substitui o sufixo 'Z' (Zulu Time) pelo offset equivalente padrão (+00:00) exigido pelo fromisoformat
                    nascimento = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    raise ValueError(f"Formato de data inválido: {value}")

        # Se o dado foi convertido ou já veio originalmente como um objeto datetime
        if isinstance(nascimento, datetime):
            # Bloqueio de integridade cronológica: a data civil de nascimento nunca pode ser maior que o dia de hoje
            if nascimento.date() > date.today():
                raise ValueError("A data de nascimento não pode ser uma data futura.")
            return nascimento  # Retorna o objeto cronológico perfeitamente estabelecido

        # Lança exceção de validação caso a entrada não seja nem string nem datetime válido
        raise ValueError("Tipo de dado inválido para data de nascimento.")


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["DataNascimento"]