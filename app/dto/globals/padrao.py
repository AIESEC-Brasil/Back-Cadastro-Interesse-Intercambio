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
    field_validator, # Decorador que permite definir funções de validação customizadas para campos específicos, garantindo integridade dos dados.
    TypeAdapter # Classe que permite criar adaptadores de tipo para conversão e validação de dados complexos, útil para integração com APIs externas.
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
    List             # Hint de tipo para representar listas/arrays de elementos de um tipo específico (ex: List[str] para lista de strings).
)

from datetime import (
    datetime,        # Objeto padrão para manipulação de carimbos de data e hora (timestamp).
    date             # Objeto padrão para manipulação de datas calendárias (dia, mês, ano).
)

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

class DivisaoMercado(BaseModel):
    """
    Estrutura para representar a divisão de mercado por Comitê Local (CL) ou Instituição.

    Attributes:
        id (int): Identificador único da divisão.
        nome (str): Nome amigável da divisão (ex: nome do CL ou Instituição).
        gv (str): Destino de roteamento para Voluntariado Global.
        gt (str): Destino de roteamento para Talentos Globais.
    """
    id: int = Field(
        description="ID interno numérico da divisão",
        json_schema_extra={
            "example": 1
        }
    )
    nome: str = Field(
        description="Nome amigável da divisão (CL ou Instituição)",
        json_schema_extra={
            "example": "Recife(PE)"
        }
    )
    gv: str = Field(
        description="Destino de roteamento para Voluntariado Global",
        json_schema_extra={
            "example": "AIESEC em Recife"
        }
    )
    gt: str = Field(
        description="Destino de roteamento para Talentos Globais",
        json_schema_extra={
            "example": "AIESEC em Recife"
        }
    )
    
    @classmethod
    def processar_lista(cls, dados) -> list:
        # Aqui está exatamente a linha que você definiu!
        # Usamos 'cls' no lugar do nome da classe para ficar dinâmico
        adapter = TypeAdapter(List[cls])
        return adapter.dump_python(adapter.validate_python(dados))

# =================================================================
# 4. EXPORTAÇÕES DO MÓDULO
# =================================================================

# Define os símbolos exportados quando o módulo é importado via 'from ... import *'
__all__ = [
    "Comite",
    "TelefoneItem",
    "EmailItem",
    "Autorizacao",
    "DataNascimento",
    "DivisaoMercado"
]