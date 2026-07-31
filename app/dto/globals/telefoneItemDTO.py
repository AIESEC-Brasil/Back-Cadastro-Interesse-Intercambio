"""Módulo de DTO para Estrutura de Telefone.

Este módulo define o modelo Pydantic `TelefoneItem`, responsável por validar,
higienizar e estruturar os dados de telefone/celular recebidos no payload,
garantindo compatibilidade com os padrões de integração da API do Podio.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from pydantic import (
    BaseModel,        # Classe base para criação de modelos de dados com validação automática.
    ConfigDict,       # Objeto de configuração para definir comportamentos do modelo (ex: proibir campos extras).
    Field,            # Utilizado para definir metadados dos campos, como descrições e exemplos para o JSON Schema.
    field_validator,  # Decorador para definir funções de validação customizadas para campos específicos.
)

# Importa o enumerador com os tipos de categorias de contato permitidas
from .categoriaContatoDTO import CategoriaContato


# =================================================================
# 2. MODELO DE DADOS (DTO)
# =================================================================

class TelefoneItem(BaseModel):
    """Estrutura para itens de telefone e celular compatível com as especificações da API do Podio.

    Mapeia os dados brutos de entrada para uma estrutura limpa e tipada contendo a etiqueta
    do telefone e o número formatado puramente como string numérica, incluindo obrigatoriamente o DDD.

    Attributes:
        tipo (CategoriaContato): Tipo de classificação do telefone (Ex: CategoriaContato.MOBILE).
        numero (str): String numérica contendo o DDD e o número telefônico limpos.
    """

    # Configuração global do modelo no Pydantic v2
    model_config = ConfigDict(
        extra="forbid"  # Rejeita estritamente campos extras não declarados no payload para maior segurança
    )

    # Classificação do tipo de contato (ex: celular, trabalho, residencial)
    tipo: CategoriaContato = Field(description="Categoria do telefone")

    # Número do telefone higienizado contendo DDD e dígitos
    numero: str = Field(
        description="Número do telefone com DDD",
        json_schema_extra={
            "example": "81999999999"  # Exemplo exibido na documentação interativa (Swagger/OpenAPI)
        },
    )

    @field_validator("numero", mode="before")
    @classmethod
    def telefone_valido(cls, numero: str) -> str:
        """Intercepta, limpa e valida a string de telefone recebida no payload bruto.

        Garante que espaços adicionais não quebrem a validação e aciona a regra
        de expressão regular do padrão celular nacional brasileiro.

        Args:
            numero (Any): O dado cru enviado no campo de número do telefone.

        Returns:
            str: O número telefônico higienizado contendo apenas dígitos numéricos válidos.

        Raises:
            ValueError: Se o telefone for nulo, vazio ou falhar no padrão nacional de 11 dígitos.
        """
        # Importação tardia (lazy import) para evitar importação circular entre módulos de utilitários
        from app.utils import validar_telefone

        # Executa limpeza removendo espaços em branco extras que costumam vir de inputs de formulários
        num_str = str(numero).strip() if numero else ""

        # Consulta a função nacional de checagem para aprovar ou rejeitar o número de telefone móvel
        if validar_telefone(num_str):
            return num_str

        # Lança exceção de validação capturada nativamente pelo Pydantic
        raise ValueError("O telefone não é um número válido ou está em branco")


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["TelefoneItem"]