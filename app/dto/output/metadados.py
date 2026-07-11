# =================================================================
# 1. IMPORTAÇÕES (DEPENDÊNCIAS)
# =================================================================
from pydantic import (
    BaseModel,       # Classe base para criação de modelos de dados com validação automática.
    EmailStr,        # Tipo de campo especializado que valida se a string segue o formato de e-mail (RFC 5322).
    Field,           # Utilizado para definir metadados dos campos, como descrições, aliases e exemplos para o JSON Schema.
    ConfigDict,      # Objeto de configuração para definir comportamentos do modelo (ex: permitir aliases, proibir campos extras).
    field_serializer, # Decorador que permite customizar como um campo específico é convertido para JSON (ex: formatar datas).
)

from typing import (
    Dict,            # Hint de tipo para representar dicionários (mapeamentos chave-valor) nas assinaturas de métodos.
    Any,             # Hint de tipo especial que indica que um valor pode ser de qualquer natureza (dinâmico).
    Union,           # Hint de tipo que permite que um campo aceite mais de um tipo de dado (ex: datetime OU string)
    List             # Hint de tipo para representar listas/arrays de elementos de um tipo específico (ex: List[str] para lista de strings).
)

from datetime import (
    datetime       # Objeto padrão para manipulação de carimbos de data e hora (timestamp).
)

from ..globals import DivisaoMercado  # Importa o DTO de Divisão de Mercado para validação e serialização

# =================================================================
# 2. METADADOS E LOGÍSTICA DE SISTEMA
# =================================================================

class Metadados(BaseModel):
    """
    Gerencia informações de rastreio técnico e payloads brutos.

    Attributes:
        data (Dict): Contém o payload original recebido para fins de log/auditoria.
        DataHora (datetime | str): Registro temporal do processamento da requisição.
    """

    cl: List[DivisaoMercado] = Field(
        title="Comitê Local (CL)",
        description="Informações de roteamento e configuração do Comitê Local (CL).",
        json_schema_extra={
            "type": "object",
            "example": {
                "nome": "Comitê Local Exemplo",
                "gv": "Roteamento GV Exemplo",
                "gt": "Roteamento GT Exemplo"
            }
        }
    )

    universidades: List[DivisaoMercado] = Field(
        title="Universidades",
        description="Mapeamento de universidades e seus respectivos roteamentos.",
        json_schema_extra={
            "type": "object",
            "example": {
                "nome": "Universidade Exemplo",
                "gv": "Roteamento GV Exemplo",
                "gt": "Roteamento GT Exemplo"
            }
        }
    )

    # 'title' personaliza o rótulo no Swagger/OpenAPI.
    # 'json_schema_extra' garante a representação correta como objeto dinâmico.
    data: List[Dict[str, Any]] = Field(
        title="Payload",
        description="Payload bruto original da requisição para auditoria",
        json_schema_extra={
            "type": "object",
            "example": {
                "app_id": 123456789,
                "fields": [
                    {
                        "label": "Gênero",
                        "type": "category",
                        "external_id": "genero",
                        "config": {
                            "settings": {
                                "options": [
                                    {"id": 1, "text": "Opção A"},
                                    {"id": 2, "text": "Opção B"}
                                ]
                            }
                        }
                    }
                ]
            }
        }
    )

    # validation_alias permite aceitar 'timestamp' no JSON e converter para 'DataHora'.
    # 'validation_alias' permite que o Pydantic procure a chave 'timestamp' no JSON de entrada,
    # mapeando-a internamente para o atributo 'DataHora'.
    # A tipagem Union aceita múltiplos formatos: objetos datetime, strings ISO, ou números (Unix Timestamp).
    DataHora: Union[datetime,str] = Field(
        validation_alias="timestamp",
        title="Timestamp de Processamento",
        description="Data e hora em que a operação foi registrada. Aceita String ISO 8601 ou Unix Timestamp e sai como ISO.",
        # Metadados estendidos para a geração do esquema JSON (Swagger/OpenAPI)
        json_schema_extra={
            "example": "2026-02-18T17:40:00Z"
        }
    )

    # Configurações do Pydantic para este modelo
    model_config = ConfigDict(
        populate_by_name=True, # Permite popular usando o nome do atributo ou o alias
        extra="forbid",       # Rejeita campos desconhecidos no payload para maior segurança
        # 'anyOf' informa à documentação que o valor pode ser validado contra diferentes esquemas,
        # refletindo a versatilidade do Pydantic em converter tipos numéricos para datetime.
    )

    @field_serializer('DataHora')
    def formatar_data_portugues(self, date_time: Union[datetime, str]) -> str:
        """
        Transforma o datetime em uma string humanizada no padrão PT-BR.

        Aplica capitalização nos nomes de dias e meses para exibição em relatórios.

        Args:
            date_time (datetime | str): O valor original do campo.

        Returns:
            str: Data formatada. Ex: "Quarta-feira, 18 de Fevereiro de 2026, 16:54:00"
        """
        # Fallback caso ocorra um erro de validação prévio e o valor seja str
        if isinstance(date_time, str):
            return date_time

        # 1. Gera a string base com nomes de dia/mês via locale
        # Resultado esperado: "quarta-feira, 18 de fevereiro de 2026, 17:35:00"
        data_formatada = date_time.strftime("%A, %d de %B de %Y, %H:%M:%S")

        # 2. Capitalização para nomes próprios de meses e dias da semana
        # O Python por padrão em PT-BR gera minúsculos.
        partes = data_formatada.split(' de ')

        if len(partes) > 1:
            # Transforma "quarta-feira, 18" em "Quarta-feira, 18"
            dia_semana_e_numero = partes[0].capitalize()

            # Transforma "fevereiro" em "Fevereiro"
            mes_nome = partes[1].capitalize()

            # Reagrupa o restante (ano e horário)
            resto_data_hora = ' de '.join(partes[2:])

            # Dicionário de tradução local na memória
            traducoes = {
                "Monday": "Segunda-feira", "Tuesday": "Terça-feira", "Wednesday": "Quarta-feira",
                "Thursday": "Quinta-feira", "Friday": "Sexta-feira", "Saturday": "Sábado", "Sunday": "Domingo",
                "January": "Janeiro", "February": "Fevereiro", "March": "Março", "April": "Abril",
                "May": "Maio", "June": "Junho", "July": "Julho", "August": "Agosto",
                "September": "Setembro", "October": "Outubro", "November": "Novembro", "December": "Dezembro"
            }

            texto_original = f"{dia_semana_e_numero} de {mes_nome} de {resto_data_hora}"

            # Substitui as palavras em inglês pelas em português localmente
            texto_traduzido = texto_original
            for eng, pt in traducoes.items():
                texto_traduzido = texto_traduzido.replace(eng, pt)

            return texto_traduzido

        # Fallback genérico de capitalização
        return data_formatada.capitalize()


__all__ = ["Metadados"]