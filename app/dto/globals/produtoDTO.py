"""Módulo de Validação e Mapeamento de Produtos de Intercâmbio.

Este módulo define o schema Pydantic `Produto` e a função auxiliar de auditoria
`validar_dados_produto`, responsáveis por garantir a integridade cadastral e a
coerência entre o título do produto, seu ID no Podio e seu ID internacional na plataforma EXPA.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from typing import (
    Self,   # Hint de tipo para indicar que o validador retorna a própria instância da classe.
    Union,  # Hint de tipo para permitir que uma função retorne múltiplos tipos (ex: bool ou str).
)

from pydantic import (
    BaseModel,        # Classe base do Pydantic para criação e validação de estruturas de dados.
    ConfigDict,       # Objeto de configuração de regras globais do modelo (ex: 'forbid' para proibir campos extras).
    Field,            # Função para declaração de metadados, descrições e exemplos OpenAPI/Swagger.
    model_validator,  # Decorador para execução de validações customizadas no nível do objeto completo.
    PositiveInt       # Tipa e valida se é inteiro e positivo
)


# =================================================================
# 2. FUNÇÕES AUXILIARES E VALIDADORES DE NEGÓCIO
# =================================================================

def validar_dados_produto(nome: str, id_podio: int, id_expa: int) -> Union[bool, str]:
    """Valida as chaves de identificação e regras de negócio de um produto de intercâmbio.

    Garante de forma integrada que o título e o ID do Podio façam correspondência estrutural
    no cache de metadados sob a tag 'status' e que o ID correspondente da plataforma internacional
    EXPA esteja listado dentro das categorias oficiais aceitas de intercâmbios ativos.

    Args:
        nome (str): Nome descritivo ou título comercial do programa (Ex: Voluntário Global).
        id_podio (int): Código numérico indexador atribuído ao campo de seleção do Podio.
        id_expa (int): Código internacional mapeado na plataforma global da AIESEC (EXPA).

    Returns:
        bool | str: True se todos os parâmetros passarem nas regras de negócio cruzadas;
                    String com o motivo do erro caso contrário.
    """
    # Importação do cache da aplicação realizada de forma tardia (lazy) para evitar import cruzado/circular
    from app.cache import cache

    # Lista de IDs internacionais permitidos e aceitos pelas regras globais (Ex: GV, GT, GE)
    list_id_expa = [7, 8, 9]

    # Variáveis de controle de fluxo para rastrear onde a validação falhou
    tem_produto = False
    tem_id_podio = False
    tem_nome_correto = False

    try:
        # Puxa o estado atualizado dos metadados extraídos da API do Podio no cache em memória
        cache_metadados = cache.store["metadados_card-ogx"]["data"]

        # Itera sobre cada campo configurado no cache de metadados
        for item in cache_metadados:
            # Localiza o campo chave que gerencia os estados/produtos do formulário no Podio
            if item.get("external_id") == "produto":
                tem_produto = True  # Marca que o campo de produto existe nos metadados

                # Itera sobre as opções pré-definidas para o campo de produto no Podio
                for opcao in item.get("options", []):
                    # Verifica se o identificador local da opção corresponde ao ID informado
                    if opcao.get("id") == id_podio:
                        tem_id_podio = True  # Marca que o ID do Podio foi localizado

                        # Valida se o título do produto bate com o texto configurado na opção (ignorando espaços nas pontas)
                        if opcao.get("text", "").strip() == nome.strip():
                            tem_nome_correto = True  # Marca que o texto do produto coincide com o ID

                            # Confirma se o programa está contido na matriz de IDs internacionais permitidos (EXPA)
                            if id_expa in list_id_expa:
                                return True  # Todas as 3 pontas de checagem batem com as definições

        # --- Retornos de mensagens de erro específicas caso algum loop ou validação falhe ---
        if not tem_produto:
            return "Não possui o extern_id produto"

        if not tem_id_podio:
            return "ID do Podio informado não foi encontrado nas opções do produto"

        if not tem_nome_correto:
            return "O nome não corresponde ao ID do Podio informado"

        # Se encontrou o produto, o ID e o nome correto, mas o ID EXPA não está na lista [7, 8, 9]
        if id_expa not in list_id_expa:
            return "ID EXPA inválido!"

    except (NameError, KeyError, TypeError):
        # Trata exceções estruturais defensivamente para evitar quebras abruptas se o cache não estiver disponível
        return "erro"

    return False


# =================================================================
# 3. MODELOS DE DADOS (SCHEMAS)
# =================================================================

class Produto(BaseModel):
    """Representa estruturalmente os programas e produtos comercializados pela AIESEC (GV, GT, GE).

    Esta classe consolida os vínculos de indexação exigidos pelo ecossistema do sistema, possuindo o título do produto,
    o ID numérico interno associado às tabelas de campos do Podio e o identificador global da plataforma internacional EXPA.

    Attributes:
        titulo (str): Nome descritivo comercial do produto de interesse (Ex: voluntario global).
        id_podio (int): ID identificador configurado e mapeado nas opções do campo do Podio.
        id_expa (int): ID de mapeamento internacional da oportunidade na plataforma EXPA.
    """

    # Configuração estrita: proíbe a inclusão de quaisquer campos adicionais não mapeados no payload
    model_config = ConfigDict(extra="forbid")

    # Título comercial de identificação do produto
    titulo: str = Field(
        description="Título de identificação do produto",
        json_schema_extra={"example": "voluntario global"},
    )

    # Identificador numérico interno correspondente à opção do produto no Podio
    id_podio: PositiveInt = Field(
        description="ID interno do produto indexado no Podio",
        json_schema_extra={"example": 1},
    )

    # Identificador numérico correspondente ao programa internacional na plataforma EXPA
    id_expa: PositiveInt = Field(
        description="ID do programa correspondente no sistema EXPA",
        json_schema_extra={"example": 7},
    )

    @model_validator(mode="after")
    def verificar_produto_no_cache(self) -> Self | None:
        """Validador de negócio executado após a desserialização que audita o produto em relação ao cache.

        Garante que o ID do Podio faça correspondência ao título do programa e que o ID EXPA
        seja um produto internacional corporativamente aceito nas regras vigentes.

        Returns:
            Self: Retorna a própria instância validada e aprovada do modelo Produto.

        Raises:
            ValueError: Caso haja divergência cadastral entre os códigos Podio, EXPA ou nome do programa.
        """
        # Encaminha os três atributos do modelo para auditoria contra o cache de metadados
        valido = validar_dados_produto(self.titulo, self.id_podio, self.id_expa)

        # Se o retorno for um booleano True, o produto está totalmente validado
        if valido is True:
            return self

        # Avalia as respostas de string de erro para disparar a exceção ValueError adequada
        if valido == "Não possui o extern_id produto":
            raise ValueError("Dados Inválidos: Não foi achado a referencia de produto")

        elif valido == "ID do Podio informado não foi encontrado nas opções do produto":
            raise ValueError("Dados Inválidos: O id do podio informado não está presente nos dados")

        elif valido == "O nome não corresponde ao ID do Podio informado":
            raise ValueError("Dados Inválidos: O nome do produto está incoerente")

        elif valido == "ID EXPA inválido!":
            raise ValueError("Dados Inválidos: O id do expa está incoerente")

        elif valido == "erro":
            raise ValueError("Metadados do Podio Não foram baixados")

        return None


# =================================================================
# 4. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["Produto"]