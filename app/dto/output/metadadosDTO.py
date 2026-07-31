"""Módulo de Metadados e Logística de Sistema.

Este módulo define a estrutura Pydantic `Metadados`, responsável pelo
armazenamento de payloads brutos originais para auditoria/logs e pela
geração e formatação humanizada em português (PT-BR) dos carimbos de data/hora.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from datetime import (
    datetime,  # Objeto padrão para manipulação de carimbos de data e hora (timestamp).
)
from typing import (
    Any,       # Hint de tipo especial que indica que um valor pode ser de qualquer natureza (dinâmico).
    Dict,      # Hint de tipo para representar dicionários (mapeamentos chave-valor) nas assinaturas de métodos.
    List,      # Hint de tipo para representar listas/arrays de elementos de um tipo específico.
    Union,     # Hint de tipo que permite que um campo aceite mais de um tipo de dado (ex: datetime OU string).
)

from pydantic import (
    BaseModel,         # Classe base para criação de modelos de dados com validação automática.
    ConfigDict,        # Objeto de configuração para definir comportamentos do modelo.
    EmailStr,          # Tipo de campo especializado que valida se a string segue o formato de e-mail (RFC 5322).
    Field,             # Utilizado para definir metadados dos campos, como descrições, aliases e exemplos para o JSON Schema.
    field_serializer,  # Decorador que permite customizar como um campo específico é convertido para JSON.
)

# Importação dos DTOs globais da aplicação
from ..globals import DivisaoMercado  # Importa o DTO de Divisão de Mercado para validação e serialização


# =================================================================
# 2. MODELOS DE DADOS (SCHEMAS)
# =================================================================

class Metadados(BaseModel):
    """Gerencia informações de rastreio técnico e payloads brutos.

    Attributes:
        data (List[Dict[str, Any]]): Contém a lista de payloads brutos originais recebidos para log e auditoria.
        DataHora (Union[datetime, str]): Registro temporal do processamento da requisição, serializado em formato PT-BR humanizado.
    """

    # Configuração global do modelo no Pydantic v2
    model_config = ConfigDict(
        populate_by_name=True,  # Permite popular o modelo usando o nome do atributo ('DataHora') ou seu alias ('timestamp')
        extra="forbid",         # Rejeita estritamente campos extras não declarados no payload para maior segurança
    )

    # Payload bruto original recebido no corpo da requisição para auditoria técnico-operacional
    data: List[Dict[str, Any]] = Field(
        title="Payload",
        description="Payload bruto original da requisição para auditoria",
        json_schema_extra={
            "type": "object",
            "example": [
                {
                    "external_id": "titulo",
                    "options": [
                        {"id": 123456, "text": "Opção 1", "status": "active"},
                        {"id": 789012, "text": "Opção 2", "status": "active"},
                    ],
                },
                {
                    "external_id": "titulo2",
                    "options": [
                        {"id": 123456, "text": "Opção 1", "status": "active"},
                        {"id": 789012, "text": "Opção 2", "status": "active"},
                    ],
                },
            ],
        },
    )

    # Carimbo de data/hora do processamento com suporte a mapeamento alternativo via alias 'timestamp'
    DataHora: Union[datetime, str] = Field(
        validation_alias="timestamp",  # Mapeia a chave 'timestamp' do JSON de entrada para este atributo
        title="Timestamp de Processamento",
        description=(
            "Data e hora em que a operação foi registrada. "
            "Aceita String ISO 8601 ou Unix Timestamp e sai como string formatada em PT-BR."
        ),
        json_schema_extra={
            "example": "2026-02-18T17:40:00Z"  # Exemplo exibido na documentação interativa (Swagger/OpenAPI)
        },
    )

    @field_serializer("DataHora")
    def formatar_data_portugues(self, date_time: Union[datetime, str]) -> str:
        """Transforma o objeto datetime em uma string humanizada no padrão PT-BR.

        Aplica tradução manual de dias e meses do inglês para o português e capitalização
        adequada para exibição em relatórios e logs.

        Args:
            date_time (Union[datetime, str]): O valor original do campo (datetime instanciado ou string fallback).

        Returns:
            str: Data formatada (Ex: "Quarta-feira, 18 de Fevereiro de 2026, 17:35:00").
        """
        # Fallback de segurança: caso o valor recebido já seja uma string, retorna sem alterar
        if isinstance(date_time, str):
            return date_time

        # 1. Gera a string base de formatação temporal via formato padrão
        data_formatada = date_time.strftime("%A, %d de %B de %Y, %H:%M:%S")

        # 2. Divide a string pelas ocorrências da preposição ' de ' para tratar partes individuais
        partes = data_formatada.split(" de ")

        if len(partes) > 1:
            # Capitaliza o dia da semana e o número (ex: "quarta-feira, 18" -> "Quarta-feira, 18")
            dia_semana_e_numero = partes[0].capitalize()

            # Capitaliza o nome do mês (ex: "fevereiro" -> "Fevereiro")
            mes_nome = partes[1].capitalize()

            # Reagrupa as partes restantes da string (ano e hora)
            resto_data_hora = " de ".join(partes[2:])

            # Tabela local de mapeamento para tradução de inglês para português PT-BR
            traducoes = {
                "Monday": "Segunda-feira",
                "Tuesday": "Terça-feira",
                "Wednesday": "Quarta-feira",
                "Thursday": "Quinta-feira",
                "Friday": "Sexta-feira",
                "Saturday": "Sábado",
                "Sunday": "Domingo",
                "January": "Janeiro",
                "February": "Fevereiro",
                "March": "Março",
                "April": "Abril",
                "May": "Maio",
                "June": "Junho",
                "July": "Julho",
                "August": "Agosto",
                "September": "Setembro",
                "October": "Outubro",
                "November": "Novembro",
                "December": "Dezembro",
            }

            # Monta a frase original concatenada
            texto_original = f"{dia_semana_e_numero} de {mes_nome} de {resto_data_hora}"

            # Substitui iterativamente os termos em inglês pelos seus equivalentes em português
            texto_traduzido = texto_original
            for eng, pt in traducoes.items():
                texto_traduzido = texto_traduzido.replace(eng, pt)

            return texto_traduzido

        # Fallback genérico de capitalização caso a divisão por ' de ' falhe
        return data_formatada.capitalize()


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["Metadados"]