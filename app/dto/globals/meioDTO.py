# Importação de hints de tipos genéricos da biblioteca padrão do Python
from typing import (
    Self,    # Hint de tipo para indicar que o validador retorna a própria instância da classe.
    Union,   # Hint de tipo para permitir que uma função retorne múltiplos tipos (ex: bool ou str).
)

# Importações de classes e funções utilitárias do Pydantic para validação e definição de schemas
from pydantic import (
    BaseModel,        # Classe base do Pydantic para criação e validação de estruturas de dados.
    ConfigDict,       # Objeto de configuração de regras globais do modelo (ex: 'forbid' para proibir campos extras).
    Field,            # Função para declaração de metadados, descrições e exemplos OpenAPI/Swagger.
    model_validator,  # Decorador para execução de validações customizadas no nível do objeto completo.
    PositiveInt,      # Tipa e valida se o número é um inteiro positivo (> 0).
)


def validar_dados_meio(nome: str, id: int) -> Union[bool, str]:
    """Valida se o par de ID e Nome do meio de contato existe e coincide no cache da aplicação.

    Args:
        nome (str): Nome da opção do meio de contato informada.
        id (int): ID identificador da opção do meio de contato no Podio.

    Returns:
        Union[bool, str]: Retorna True se a validação for bem-sucedida ou uma mensagem
        string descrevendo o motivo da falha.
    """
    # Importação do cache realizada de forma tardia (lazy import) para evitar importação circular/cruzada
    from app.cache import cache

    # Variáveis de controle para rastrear em qual etapa a validação falhar
    tem_meio = False
    tem_id_meio = False

    try:
        # Acessa a estrutura de dicionários aninhados salvos no repositório do cache
        cache_metadados = cache.store["metadados_card-ogx"]["data"]

        # Percorre os blocos de configuração contidos no JSON retornado
        for item in cache_metadados:
            # Filtra apenas o bloco de chaves mapeado para o meio de contato (como conheceu a AIESEC)
            if item.get("external_id") == "tag-meio-2-2":
                tem_meio = True  # Encontrou o bloco do meio no cache

                # Itera sobre o array de opções ativas configuradas no Podio para este campo
                for opcao in item.get("options", []):
                    # Localiza o nó cujo identificador seja idêntico ao ID que estamos validando
                    if opcao.get("id") == id:
                        tem_id_meio = True  # O ID enviado existe nas opções ativas

                        # Realiza a comparação limpando lacunas de espaçamento nas extremidades das strings
                        if opcao.get("text", "").strip() == nome.strip():
                            return True  # Validação bem-sucedida: par ID e Nome é idêntico ao oficial do Podio

        # --- Retornos de erro exatos após verificar todo o cache ---
        if not tem_meio:
            return "Não possui o external_id tag-meio-2-2 no cache"

        if not tem_id_meio:
            return "ID do meio de contato informado não foi encontrado nas opções"
        else:
            return "O nome do meio de contato não corresponde ao ID informado"

    except (NameError, KeyError, TypeError):
        # Captura exceções de chave inexistente ou estrutura nula caso o cache não esteja carregado
        return "erro"


class Meio(BaseModel):
    """Modelo Pydantic que representa o meio de contato e valida dados via cache do Podio."""

    # Configuração global do modelo no Pydantic v2
    model_config = ConfigDict(
        extra="forbid"  # Rejeita estritamente campos extras não declarados no payload para maior segurança
    )

    id: PositiveInt = Field(
        ...,
        description="ID do meio de contato de como conheceu a AIESEC",
        json_schema_extra={"example": 11},
    )
    nome: str = Field(
        ...,
        description="Nome do meio de contato de como conheceu a AIESEC",
        json_schema_extra={"example": "ads"},
    )

    @model_validator(mode="after")
    def verificar_meio_no_cache(self) -> Self | None:
        """Validador de negócio executado após a higienização que audita o meio de contato em relação ao cache.

        Garante de forma cruzada que o ID informado exista no escopo correto e que o nome
        corresponda exatamente à opção cadastrada no cache de metadados do Podio.

        Returns:
            Self | None: Retorna a própria instância validada do modelo Meio.

        Raises:
            ValueError: Caso haja divergência cadastral entre o ID do meio e o nome informado.
        """
        # Encaminha as chaves consolidadas do modelo para auditoria contra os metadados ativos
        valido = validar_dados_meio(nome=self.nome, id=self.id)

        if valido is True:
            return self

        # Comparação de erro idêntica caractere por caractere para levantar exceções de validação apropriadas
        if valido == "Não possui o external_id tag-meio-2-2 no cache":
            raise ValueError("Dados Inválidos: Não foi achada a referência do meio de contato local")

        elif valido == "ID do meio de contato informado não foi encontrado nas opções":
            raise ValueError("Dados Inválidos: O ID do meio de contato informado não está presente nos dados")

        elif valido == "O nome do meio de contato não corresponde ao ID informado":
            raise ValueError("Dados Inválidos: O nome do meio de contato está incoerente com o ID informado")

        elif valido == "erro":
            raise ValueError("Metadados do Podio não foram baixados")

        return None

__all__ =["Meio"]