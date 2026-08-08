"""
Módulo de DTO para Estrutura de Área de Atuação (AIESEC).

Este módulo define o modelo Pydantic `AreaAtuacao` e a função de validação cruzada
`validar_dados_area_atuacao`, responsáveis por auditar se o ID e o nome da área
de atuação informados na requisição coincidem com os metadados ativos armazenados no cache do sistema.
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

def validar_dados_area_atuacao(id_area: int, nome_area: str) -> Union[bool, str]:
    """
    Varre a base de dados do cache local de metadados para confirmar a integridade da área de atuação.

    Verifica de forma cruzada se o ID informado existe dentro do escopo do campo 'qual-sua-area-de-atuacao'
    e se o nome correspondente naquele nó de dados é equivalente ao nome enviado pelo payload da API.

    Args:
        id_area (int): Identificador numérico inteiro que descreve a área de atuação.
        nome_area (str): Nome descritivo da área de atuação fornecido pelo usuário ou formulário.

    Returns:
        Union[bool, str]: True se o ID e o Nome coincidirem com os registros do cache;
                          String com a mensagem exata do erro caso contrário.
    """
    # Importação tardia (lazy import) do objeto de cache global para evitar importação circular
    from app.cache import cache

    # Variáveis de controle para rastrear em qual etapa a validação falhar
    tem_area = False
    tem_id_area = False

    try:
        # Acessa a estrutura de dicionários aninhados salvos no repositório do cache
        cache_metadados = cache.store["metadados_card-ogx"]["data"]

        # Percorre os blocos de configuração contidos no JSON retornado
        for item in cache_metadados:
            # Filtra apenas o bloco de chaves mapeado para a seletora de área de atuação
            if item.get("external_id") == "qual-sua-area-de-atuacao":
                tem_area = True  # Encontrou o bloco de área de atuação no cache

                # Itera sobre o array de opções ativas configuradas no Podio para este campo
                for opcao in item.get("options", []):
                    # Localiza o nó cujo identificador seja idêntico ao ID que estamos validando
                    if opcao.get("id") == id_area:
                        tem_id_area = True  # O ID enviado existe nas opções

                        # Realiza o isolamento de strings limpando lacunas de espaçamento antes da igualdade
                        if opcao.get("text", "").strip() == nome_area.strip():
                            return True  # Validação bem-sucedida: par ID e Nome é idêntico ao oficial

        # --- Retornos de erro exatos após sair de todos os loops ---
        if not tem_area:
            return "Não possui o extern_id qual-sua-area-de-atuacao"

        if not tem_id_area:
            return "ID da área de atuação informado não foi encontrado nas opções"
        else:
            return "O nome da área de atuação não corresponde ao ID informado"

    except (NameError, KeyError, TypeError):
        # Captura e neutraliza exceções de escopo ou de estrutura nula caso o cache não esteja carregado
        return "erro"


# =================================================================
# 3. ESTRUTURA DO MODELO (DTO)
# =================================================================

class AreaAtuacao(BaseModel):
    """
    Representa formalmente a Área de Atuação dentro do ecossistema.

    Esta classe realiza validação cruzada tardia (`mode="after"`) garantindo que nenhuma entidade
    seja criada se o ID numérico e o Nome descritivo da área não tiverem uma correspondência
    exata e idêntica na tabela de metadados ativa do cache do sistema.

    Attributes:
        id (PositiveInt): Código numérico indexador único que identifica a área no Podio.
        nome (str): Nome da área de atuação cadastrada no Podio (Ex: Tecnologia da Informação).
    """

    # Configuração global do modelo no Pydantic v2
    model_config = ConfigDict(extra="ignore")

    # Código ID numérico único da área de atuação cadastrado no Podio
    id: PositiveInt = Field(
        description="Id da área de atuação no podio",
        json_schema_extra={"example": 12},
    )

    # Nome descritivo de exibição da área de atuação no Podio
    nome: str = Field(
        description="nome da área de atuação no podio",
        json_schema_extra={"example": "Tecnologia da Informação"},
    )

    # =================================================================
    # 4. FUNÇÕES AUXILIARES / VALIDADORAS DE CAMPO
    # =================================================================

    @model_validator(mode="after")
    def verificar_area_atuacao_no_cache(self) -> Self | None:
        """
        Validador de negócio executado após a higienização que audita a área de atuação em relação ao cache.

        Garante de forma cruzada que o ID informado exista no escopo correto e que o nome
        corresponda exatamente à opção cadastrada no cache de metadados do Podio.

        Returns:
            Self | None: Retorna a própria instância validada do modelo de AreaAtuacao.

        Raises:
            ValueError: Caso haja divergência cadastral entre o ID da área e o nome informado.
        """
        # Encaminha as chaves consolidadas do modelo para auditoria contra os metadados ativos
        valido = validar_dados_area_atuacao(self.id, self.nome)

        if valido is True:
            return self

        # Comparação de erro idêntica caractere por caractere para levantar exceções de validação apropriadas
        if valido == "Não possui o extern_id qual-sua-area-de-atuacao":
            raise ValueError("Dados Inválidos: Não foi achada a referência de área de atuação")

        elif valido == "ID da área de atuação informado não foi encontrado nas opções":
            raise ValueError("Dados Inválidos: O id da área de atuação informado não está presente nos dados")

        elif valido == "O nome da área de atuação não corresponde ao ID informado":
            raise ValueError("Dados Inválidos: O nome da área de atuação está incoerente")

        elif valido == "erro":
            raise ValueError("Metadados do Podio Não foram baixados")

        return None


# =================================================================
# 5. EXPORTAÇÃO CONSOLIDADA DO MÓDULO
# =================================================================

__all__ = ["AreaAtuacao"]