"""
Módulo de DTO para Estrutura de Idioma (AIESEC).

Este módulo define o modelo Pydantic `Idioma` e a função de validação cruzada
`validar_dados_idioma`, responsáveis por auditar se o ID e o nome do idioma
informados na requisição coincidem com os metadados ativos armazenados no cache do sistema.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================

# Módulos nativos do Python para suporte a anotações de tipos
from typing import (
    Self,   # Hint de tipo para indicar que o método retorna a própria instância da classe.
    Union,  # Hint de tipo para declarar que uma função aceita ou retorna mais de um tipo de dado.
)

# Importações do Pydantic (versão 2) utilizadas na construção e validação da estrutura de dados:
from pydantic import (
    BaseModel,        # Classe base para criação de modelos de dados com validação automática.
    ConfigDict,       # Objeto de configuração para definir comportamentos do modelo.
    Field,            # Utilizado para definir metadados dos campos (descrições, exemplos, etc).
    model_validator,  # Decorador para aplicar regras de validação no nível do modelo completo.
    PositiveInt,      # Tipa e valida se é inteiro e positivo.
)


# =================================================================
# 2. FUNÇÃO DE VALIDAÇÃO DE NEGÓCIO (CACHE METADADOS)
# =================================================================

def validar_dados_idioma(id_idioma: int, nome_idioma: str) -> Union[bool, str]:
    """
    Varre a base de dados do cache local de metadados para confirmar a integridade de um idioma.

    Verifica de forma cruzada se o ID informado existe dentro do escopo do campo 'possui-outro-idioma'
    e se o nome correspondente naquele nó de dados é equivalente ao nome enviado pelo payload da API.

    Args:
        id_idioma (int): Identificador numérico inteiro que descreve o idioma.
        nome_idioma (str): Nome descritivo do idioma fornecido pelo usuário ou formulário.

    Returns:
        Union[bool, str]: True se o ID e o Nome coincidirem com os registros do cache;
                          String com a mensagem exata do erro caso contrário.
    """
    # Importação tardia (lazy import) do objeto de cache global para evitar importação circular
    from app.cache import cache

    # Variáveis de controle para rastrear em qual etapa a validação falhar
    tem_idioma = False
    tem_id_idioma = False

    try:
        # Acessa a estrutura de dicionários aninhados salvos no repositório do cache
        cache_metadados = cache.store["metadados_card-ogx"]["data"]

        # Percorre os blocos de configuração contidos no JSON retornado
        for item in cache_metadados:
            # Filtra apenas o bloco de chaves mapeado para a seletora de idiomas da AIESEC
            if item.get("external_id") == "possui-outro-idioma":
                tem_idioma = True  # Encontrou o bloco de idioma no cache

                # Itera sobre o array de opções ativas configuradas no Podio para este campo
                for opcao in item.get("options", []):
                    # Localiza o nó cujo identificador seja idêntico ao ID que estamos validando
                    if opcao.get("id") == id_idioma:
                        tem_id_idioma = True  # O ID enviado existe nas opções

                        # Realiza o isolamento de strings limpando lacunas de espaçamento antes da igualdade
                        if opcao.get("text", "").strip() == nome_idioma.strip():
                            return True  # Validação bem-sucedida: par ID e Nome é idêntico ao oficial

        # --- Retornos de erro exatos após sair de todos os loops ---
        if not tem_idioma:
            return "Não possui o extern_id possui-outro-idioma"

        if not tem_id_idioma:
            return "ID do idioma informado não foi encontrado nas opções"
        else:
            return "O nome do idioma não corresponde ao ID informado"

    except (NameError, KeyError, TypeError):
        # Captura e neutraliza exceções de escopo ou de estrutura nula caso o cache não esteja carregado
        return "erro"


# =================================================================
# 3. ESTRUTURA DO MODELO (DTO)
# =================================================================

class Idioma(BaseModel):
    """
    Representa formalmente um Idioma dentro do ecossistema.

    Esta classe realiza validação cruzada tardia (`mode="after"`) garantindo que nenhuma entidade
    seja criada se o ID numérico e o Nome descritivo do idioma não tiverem uma correspondência
    exata e idêntica na tabela de metadados ativa do cache do sistema.

    Attributes:
        id (PositiveInt): Código numérico indexador único que identifica o idioma no Podio.
        nome (str): Nome do idioma e seu nível cadastrado no Podio (Ex: Inglês-Intermediário).
    """

    # Configuração global do modelo no Pydantic v2
    model_config = ConfigDict(extra="ignore")

    # Código ID numérico único do idioma cadastrado no Podio
    id: PositiveInt = Field(
        description="Id do idioma no podio",
        json_schema_extra={"example": 32},
    )

    # Nome descritivo de exibição do idioma no Podio
    nome: str = Field(
        description="nome do idioma no podio",
        json_schema_extra={"example": "Inglês-Intermediário"},
    )

    # =================================================================
    # 4. FUNÇÕES AUXILIARES / VALIDADORAS DE CAMPO
    # =================================================================

    @model_validator(mode="after")
    def verificar_idioma_no_cache(self) -> Self | None:
        """
        Validador de negócio executado após a higienização que audita o idioma em relação ao cache.

        Garante de forma cruzada que o ID informado exista no escopo correto e que o nome
        corresponda exatamente à opção cadastrada no cache de metadados do Podio.

        Returns:
            Self | None: Retorna a própria instância validada do modelo de Idioma.

        Raises:
            ValueError: Caso haja divergência cadastral entre o ID do idioma e o nome informado.
        """
        # Encaminha as chaves consolidadas do modelo para auditoria contra os metadados ativos
        valido = validar_dados_idioma(self.id, self.nome)

        if valido is True:
            return self

        # Comparação de erro idêntica caractere por caractere para levantar exceções de validação apropriadas
        if valido == "Não possui o extern_id possui-outro-idioma":
            raise ValueError("Dados Inválidos: Não foi achada a referência de idioma")

        elif valido == "ID do idioma informado não foi encontrado nas opções":
            raise ValueError("Dados Inválidos: O id do idioma informado não está presente nos dados")

        elif valido == "O nome do idioma não corresponde ao ID informado":
            raise ValueError("Dados Inválidos: O nome do idioma está incoerente")

        elif valido == "erro":
            raise ValueError("Metadados do Podio Não foram baixados")

        return None


# =================================================================
# 5. EXPORTAÇÃO CONSOLIDADA DO MÓDULO
# =================================================================

__all__ = ["Idioma"]