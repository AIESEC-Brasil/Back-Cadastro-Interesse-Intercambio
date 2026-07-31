"""Módulo de DTO para Estrutura de E-mail.

Este módulo define o modelo Pydantic `EmailItem`, responsável por validar,
higienizar e estruturar os dados de e-mail recebidos no payload, garantindo
que a categoria informada seja compatível com canais digitais e que o endereço
eletrônico siga os padrões RFC.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from pydantic import (
    BaseModel,        # Classe base para criação de modelos de dados com validação automática.
    ConfigDict,       # Objeto de configuração para definir comportamentos do modelo (ex: proibir campos extras).
    EmailStr,         # Tipo de campo especializado que valida se a string segue o formato de e-mail (RFC 5322).
    Field,            # Utilizado para definir metadados dos campos, como descrições e exemplos para o JSON Schema.
    field_validator,  # Decorador para definir funções de validação customizadas para campos específicos.
)

# Importa o enumerador com os tipos de categorias de contato permitidas
from .categoriaContatoDTO import CategoriaContato


# =================================================================
# 2. MODELO DE DADOS (DTO)
# =================================================================

class EmailItem(BaseModel):
    """Estrutura para itens de e-mail categorizados e validados.

    Esta classe gerencia pares contendo a categoria do canal de contato digital (tipo)
    e o endereço eletrônico correspondente, aplicando filtros estritos para impedir
    que e-mails utilizem marcações exclusivas de telefonia fixa ou móvel.

    Attributes:
        tipo (CategoriaContato): Classificação da etiqueta de contato (ex: 'home', 'work').
        email (EmailStr): O endereço de e-mail validado sintática e estruturalmente pelas RFCs.
    """

    # Configuração global do modelo no Pydantic v2
    model_config = ConfigDict(
        extra="forbid"  # Rejeita estritamente campos extras não declarados no payload para maior segurança
    )

    # Classificação do tipo/etiqueta do e-mail (ex: trabalho, pessoal, outro)
    tipo: CategoriaContato = Field(description="Categoria ou etiqueta do e-mail")

    # Endereço de e-mail higienizado e validado
    email: EmailStr = Field(
        description="Endereço de e-mail em formato válido",
        json_schema_extra={
            "example": "teste@gmail.com"  # Exemplo exibido na documentação interativa (Swagger/OpenAPI)
        },
    )

    @field_validator("tipo", mode="before")
    @classmethod
    def tipo_valido(cls, tipo: CategoriaContato) -> CategoriaContato:
        """Validador que barra a atribuição de etiquetas de telefonia ou fax para instâncias de e-mail.

        Args:
            tipo (CategoriaContato): Categoria informada antes da consolidação do objeto.

        Returns:
            CategoriaContato: A categoria higienizada aprovada.

        Raises:
            ValueError: Se a categoria informada pertencer ao grupo exclusivo de mobile ou fax.
        """
        # Define o conjunto de chaves de enumeração cujo uso é permitido para e-mails
        lista_tipo_permitido = {
            CategoriaContato.OTHER,
            CategoriaContato.WORK,
            CategoriaContato.HOME,
        }

        # Libera a criação do modelo caso o usuário tente associar uma etiqueta válida a um e-mail
        if tipo in lista_tipo_permitido:
            return tipo

        # Lança exceção de validação para categorias exclusivas de voz/fax
        raise ValueError(f"A categoria '{tipo}' não é permitida para endereços de e-mail.")

    @field_validator("email", mode="before")
    @classmethod
    def email_valido(cls, email: str) -> str:
        """Intercepta o e-mail bruto recebido no payload para fins de higienização de strings e pré-validação.

        Executa o isolamento e remoção de espaços em branco antes que o motor de tipos
        do Pydantic faça o processamento nativo do `EmailStr`.

        Args:
            email (Any): O valor do e-mail capturado na forma original em que foi transmitido.

        Returns:
            str: String limpa se passar nos filtros regex customizados.

        Raises:
            ValueError: Se a entrada estiver nula, em branco ou possuir formato inválido.
        """
        # Importação tardia (lazy import) para evitar importação circular entre módulos de utilitários
        from app.utils import validar_email

        # Converte o dado de entrada para string padrão e remove espaços invisíveis das bordas
        email_str = str(email).strip() if email else ""

        # Aciona o motor regex auxiliar para verificar se o e-mail possui corpo e formato válidos
        if validar_email(email_str):
            return email_str

        # Lança exceção capturada nativamente pelo Pydantic caso falhe no regex ou este esteja em branco
        raise ValueError("O email não é um e-mail válido ou está em branco")


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["EmailItem"]