from pydantic import (
    BaseModel,       # Classe base para criação de modelos de dados com validação automática.
    EmailStr,        # Tipo de campo especializado que valida se a string segue o formato de e-mail (RFC 5322).
    Field,           # Utilizado para definir metadados dos campos, como descrições, aliases e exemplos para o JSON Schema.
    field_validator, # Decorador que permite definir funções de validação customizadas para campos específicos, garantindo integridade dos dados.
    ConfigDict       # Objeto de configuração para definir comportamentos do modelo (ex: permitir aliases, proibir campos extras).
)

from .categoriaContatoDTO import CategoriaContato # Estrutura permitida para as categorias de contato

class EmailItem(BaseModel):
    """
    Estrutura para itens de e-mail categorizados e validados.

    Esta classe gerencia pares contendo a categoria do canal de contato digital (tipo)
    e o endereço eletrônico correspondente, aplicando filtros estritos para impedir
    que e-mails utilizem marcações exclusivas de telefonia fixa ou móvel.

    Attributes:
        tipo (CategoriaContato): Classificação da etiqueta de contato (ex: 'home', 'work').
        email (EmailStr): O endereço de e-mail validado sintática e estruturalmente pelas RFCs.
    """
    model_config = ConfigDict(extra='forbid')
    tipo: CategoriaContato = Field(description="Categoria ou etiqueta do e-mail")
    email: EmailStr = Field(
        description="Endereço de e-mail em formato válido",
        json_schema_extra={
            "example": "teste@gmail.com"
        }
    )

    @field_validator('tipo', mode="before")
    @classmethod
    def tipo_valido(cls, tipo: CategoriaContato) -> CategoriaContato:
        """
        Validador que barra a atribuição de etiquetas de telefonia ou fax para instâncias de e-mail.

        Args:
            tipo (CategoriaContato): Categoria informada antes da consolidação do objeto.

        Returns:
            CategoriaContato: A categoria higienizada aprovada.

        Raises:
            ValueError: Se a categoria informada pertencer ao grupo exclusivo de mobile ou fax.
        """
        # Define o conjunto de chaves de enumeração cujo uso é restrito a canais de voz/telefonia
        lista_tipo_permitido = {
            CategoriaContato.OTHER,
            CategoriaContato.WORK,
            CategoriaContato.HOME
        }

        # Libera a criação do modelo caso o usuário tente associar uma etiqueta valida a um e-mail
        if tipo in lista_tipo_permitido:
            return tipo
        raise ValueError(f"A categoria '{tipo}' não é permitida para endereços de e-mail.")

    @field_validator('email', mode="before")
    @classmethod
    def email_valido(cls, email: str) -> str:
        """
        Intercepta o e-mail bruto recebido no payload para fins de higienização de strings e pré-validação.

        Executa o isolamento e remoção de espaços em branco antes que o motor de tipos
        do Pydantic faça o processamento nativo do `EmailStr`.

        Args:
            email (Any): O valor do e-mail capturado na forma original em que foi transmitido.

        Returns:
            Any: String limpa se passar nos filtros regex customizados.

        Raises:
            ValueError: Se a entrada estiver nula, em branco ou possuir formato inválido.
        """
        from app.utils import validar_email # Função de validação de e-mail verificando o formato
        # Converte o dado de entrada para string padrão e remove espaços invisíveis das bordas
        email_str = str(email).strip() if email else ""

        # Aciona o motor regex auxiliar para verificar se o e-mail possui corpo e formato válidos
        if validar_email(email_str):
            return email_str
        raise ValueError("O email não é um e-mail válido ou está em branco")

__all__ = ["EmailItem"]