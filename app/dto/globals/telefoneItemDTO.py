from pydantic import (
    BaseModel,       # Classe base para criação de modelos de dados com validação automática.
    EmailStr,        # Tipo de campo especializado que valida se a string segue o formato de e-mail (RFC 5322).
    Field,           # Utilizado para definir metadados dos campos, como descrições, aliases e exemplos para o JSON Schema.
    field_validator, # Decorador que permite definir funções de validação customizadas para campos específicos, garantindo integridade dos dados.
    ConfigDict       # Objeto de configuração para definir comportamentos do modelo (ex: permitir aliases, proibir campos extras).
)

from .categoriaContatoDTO import CategoriaContato # Estrutura permitida para as categorias de contato

class TelefoneItem(BaseModel):
    """
    Estrutura para itens de telefone e celular compatível com as especificações da API do Podio.

    Mapeia os dados brutos de entrada para uma estrutura limpa e tipada contendo a etiqueta
    do telefone e o número formatado puramente como string numérica, incluindo obrigatoriamente o DDD.

    Attributes:
        tipo (CategoriaContato): Tipo de classificação do telefone (Ex: CategoriaContato.MOBILE).
        numero (str): String numérica contendo o DDD e o número telefônico limpos.
    """
    model_config = ConfigDict(extra='forbid')
    tipo: CategoriaContato = Field(description="Categoria do telefone")
    numero: str = Field(
        description="Número do telefone com DDD",
        json_schema_extra={
            "example": "81999999999"
        }
    )

    @field_validator('numero', mode="before")
    @classmethod
    def telefone_valido(cls, numero: str) -> str:
        """
        Intercepta, limpa e valida a string de telefone recebida no payload bruto.

        Garante que espaços adicionais não quebrem a validação e aciona a regra
        de expressão regular do padrão celular nacional brasileiro.

        Args:
            numero (Any): O dado cru enviado no campo de número do telefone.

        Returns:
            str: O número telefônico higienizado contendo apenas dígitos numéricos válidos.

        Raises:
            ValueError: Se o telefone for nulo, vazio ou falhar no padrão nacional de 11 dígitos.
        """
        from app.utils import validar_telefone # Função de validação de telefone verificando o formato
        # Executa limpeza removendo espaços em branco extras que costumam vir de inputs de formulários
        num_str = str(numero).strip() if numero else ""

        # Consulta a função nacional de checagem para aprovar ou rejeitar o número de telefone móvel
        if validar_telefone(num_str):
            return num_str
        raise ValueError("O telefone não é um número válido ou está em branco")

__all__ = ["TelefoneItem"]