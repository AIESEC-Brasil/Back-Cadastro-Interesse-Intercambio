"""
Módulo de Submodelos de Apoio para DTOs (Data Transfer Objects).

Este arquivo define estruturas de dados compartilhadas que compõem múltiplos
objetos de transferência de dados no sistema, garantindo validação rigorosa
e formatação amigável para integração com APIs (ex: Podio) e interfaces de usuário.
"""

# =================================================================
# 1. IMPORTAÇÕES (DEPENDÊNCIAS)
# =================================================================
from pydantic import (
    BaseModel,       # Classe base para criação de modelos de dados com validação automática.
    EmailStr,        # Tipo de campo especializado que valida se a string segue o formato de e-mail (RFC 5322).
    Field,           # Utilizado para definir metadados dos campos, como descrições, aliases e exemplos para o JSON Schema.
    ConfigDict,      # Objeto de configuração para definir comportamentos do modelo (ex: permitir aliases, proibir campos extras).
    field_serializer, # Decorador que permite customizar como um campo específico é convertido para JSON (ex: formatar datas).
    field_validator
)
from pydantic_core import (
    core_schema      # Fornece acesso às estruturas de baixo nível do Pydantic para criar validadores customizados complexos.
)
from enum import (
    Enum,            # Classe base para criar enumeradores de strings, garantindo conjuntos fixos de opções.
    IntEnum          # Variante de enumerador onde os membros são comparáveis a inteiros, ideal para flags numéricas.
)
from typing import (
    Dict,            # Hint de tipo para representar dicionários (mapeamentos chave-valor) nas assinaturas de métodos.
    Any,             # Hint de tipo especial que indica que um valor pode ser de qualquer natureza (dinâmico).
    Union,           # Hint de tipo que permite que um campo aceite mais de um tipo de dado (ex: datetime OU string).
)

from datetime import (
    datetime,        # Objeto padrão para manipulação de carimbos de data e hora (timestamp).
    date             # Objeto padrão para manipulação de datas calendárias (dia, mês, ano).
)

from deep_translator import GoogleTranslator

# =================================================================
# 2. ENUMS E TIPOS CONSTANTES
# =================================================================

class CategoriaContato(str, Enum):
    """
    Categorias de contato aceitas, padronizadas para integração com o Podio.

    Herda de (str, Enum) para garantir a serialização correta como string no JSON
    e permitir comparações diretas com strings.
    """
    HOME = "home"                 # Uso residencial/pessoal
    WORK = "work"                 # Uso profissional/corporativo
    MOBILE = "mobile"             # Dispositivo móvel/celular
    MAIN = "main"                 # Contato principal
    OTHER = "other"               # Outras categorias não listadas
    PRIVATE_FAX = "private_fax"   # Fax pessoal
    WORK_FAX = "work_fax"         # Fax profissional

class Autorizacao(IntEnum):
    """
    Enumeração para representação binária de estados de consentimento e autorização.

    Esta classe utiliza IntEnum para garantir que os valores sejam tratados como
    inteiros (0 ou 1), facilitando a integração com APIs de terceiros (como Podio)
    e bancos de dados que não suportam tipos booleanos nativos de forma flexível.

    Members:
        SIM (int): Representa o estado positivo/verdadeiro (1) de autorização.
        NAO (int): Representa o estado negativo/falso (0) de autorização.
    """
    # Valor inteiro representando autorização concedida
    SIM = 1
    # Valor inteiro representando autorização negada
    NAO = 0


# =================================================================
# 3. SUB-MODELOS DE APOIO
# =================================================================

class EmailItem(BaseModel):
    """
    Estrutura para itens de e-mail categorizados.

    Attributes:
        tipo (CategoriaContato): Define a categoria do e-mail (ex: 'home', 'work').
        email (EmailStr): O endereço de e-mail com validação sintática RFC.
    """
    # Categoria/Etiqueta do endereço de e-mail (ex: pessoal, trabalho)
    tipo: CategoriaContato = Field(description="Categoria do e-mail")

    # Endereço de e-mail validado sintaticamente pelo Pydantic
    email: EmailStr = Field(
        description="Endereço de e-mail válido",
        json_schema_extra={
            "example": "teste@gmail.com"
        }
    )

    @field_validator('tipo', mode="before")
    @classmethod
    def tipo_valido(cls, tipo: CategoriaContato) -> CategoriaContato:
        """Valida se a categoria do e-mail é permitida.

            Args:
                tipo: Categoria a ser validada.

            Returns:
                CategoriaContato: A categoria validada.

            Raises:
                ValueError: Se o tipo for exclusivo de dispositivos móveis/fax.
        """
        lista_exclusivo_tipo_mobile = {
            CategoriaContato.MOBILE,
            CategoriaContato.MAIN,
            CategoriaContato.PRIVATE_FAX,
            CategoriaContato.WORK_FAX
        }
        #verifica se o tipo é um tipo exclusivo do mobile
        if tipo in lista_exclusivo_tipo_mobile:
            raise ValueError(f"A categoria '{tipo}' não é permitida para endereços de e-mail.")
        return tipo


class TelefoneItem(BaseModel):
    """
    Estrutura para itens de telefone compatível com a API do Podio.

    Attributes:
        tipo (CategoriaContato): Define se o telefone é residencial, móvel, etc.
        numero (str): O número de telefone formatado como string.
    """
    # Categoria/Etiqueta do número de telefone (ex: celular, fixo)
    tipo: CategoriaContato = Field(
        description="Categoria do telefone"
    )


    # String contendo o número de telefone (geralmente apenas dígitos)
    numero: str = Field(
        description="Número do telefone com DDD",
        json_schema_extra = {
            "example": "81999999999"
        }
    )


class Comite(BaseModel):
    """
    Representa o Comitê Local (Unidade da AIESEC) no sistema.

    Attributes:
        id (int): Identificador numérico único do comitê.
        nome (str): Nome amigável da unidade local para exibição.
    """
    # ID interno da entidade mapeado no Podio ou banco de dados
    id: int = Field(
        description="ID interno numérico da entidade",
        json_schema_extra={
            "example": 32
        }
    )

    # Nome textual para identificação do usuário final
    nome: str = Field(
        description="Nome amigável da unidade (Comitê Local)",
        json_schema_extra={
            "example": "Recife(PE)"
        }
    )


class DataNascimento:
    """
    Classe utilitária para validação e parse de datas de nascimento.

    Diferente de outros modelos, não herda de BaseModel para atuar como um
    tipo primitivo validado, evitando o aninhamento de chaves no JSON final.
    """

    @classmethod
    def __get_pydantic_core_schema__(
            cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        """
        Define o esquema de núcleo do Pydantic para esta classe.

        Permite que a classe seja usada como um tipo em outros modelos Pydantic,
        aplicando a lógica de validação customizada antes da conversão para datetime.
        """
        return core_schema.no_info_before_validator_function(
            cls.validar,
            core_schema.datetime_schema(),  # Define o tipo final esperado como datetime
        )

    @staticmethod
    def validar(value: Any) -> datetime:
        """
        Lógica de normalização de strings e impedimento de datas futuras.

        Args:
            value (Any): Valor de entrada para validação (string ou datetime).

        Returns:
            datetime: Objeto datetime validado.

        Raises:
            ValueError: Se o formato for inválido ou a data for posterior a hoje.
        """
        nascimento = value

        # Processamento caso a entrada seja uma string
        if isinstance(value, str):
            # Tenta converter utilizando formatos de data comuns
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    nascimento = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue

            # Caso não tenha casado com os formatos acima, tenta o padrão ISO 8601
            if isinstance(nascimento, str):
                try:
                    # Normaliza o sufixo 'Z' para offset UTC caso presente
                    nascimento = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    raise ValueError(f"Formato de data inválido: {value}")

        # Validação de integridade cronológica
        if isinstance(nascimento, datetime):
            # Impede que a data de nascimento seja maior que a data atual do servidor
            if nascimento.date() > date.today():
                raise ValueError("A data de nascimento não pode ser uma data futura.")
            return nascimento

        raise ValueError("Tipo de dado inválido para data de nascimento.")

    def strftime(self, param:str):
        pass


# =================================================================
# 4. METADADOS E LOGÍSTICA DE SISTEMA
# =================================================================

class Metadados(BaseModel):
    """
    Gerencia informações de rastreio técnico e payloads brutos.

    Attributes:
        data (Dict): Contém o payload original recebido para fins de log/auditoria.
        DataHora (datetime | str): Registro temporal do processamento da requisição.
    """

    # 'title' personaliza o rótulo no Swagger/OpenAPI.
    # 'json_schema_extra' garante a representação correta como objeto dinâmico.
    data: Dict[str, Any] = Field(
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

            return GoogleTranslator(source='auto', target='pt').translate(f"{dia_semana_e_numero} de {mes_nome} de {resto_data_hora}")

        # Fallback genérico de capitalização
        return data_formatada.capitalize()


# =================================================================
# 4. EXPORTAÇÕES DO MÓDULO
# =================================================================

# Define os símbolos exportados quando o módulo é importado via 'from ... import *'
__all__ = [
    "Comite",
    "TelefoneItem",
    "EmailItem",
    "Metadados",
    "Autorizacao",
    "DataNascimento"
]