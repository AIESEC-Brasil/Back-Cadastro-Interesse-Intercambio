"""
Módulo de DTO para Estrutura de Nível de Atuação (AIESEC).

Este módulo define o modelo Pydantic `NivelAtuacao` e a função de validação cruzada
`validar_dados_nivel_atuacao`, responsáveis por auditar se o ID e o nome do nível
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

def validar_dados_nivel_atuacao(id_nivel: int, nome_nivel: str) -> Union[bool, str]:
    """
    Varre a base de dados do cache local de metadados para confirmar a integridade do nível de atuação.

    Verifica de forma cruzada se o ID informado existe dentro do escopo do campo 'qual-seu-nivel-de-atuacao'
    e se o nome correspondente naquele nó de dados é equivalente ao nome enviado pelo payload da API.

    Args:
        id_nivel (int): Identificador numérico inteiro que descreve o nível de atuação.
        nome_nivel (str): Nome descritivo do nível de atuação fornecido pelo usuário ou formulário.

    Returns:
        Union[bool, str]: True se o ID e o Nome coincidirem com os registros do cache;
                          String com a mensagem exata do erro caso contrário.
    """
    # Importação tardia (lazy import) do objeto de cache global para evitar importação circular
    from app.cache import cache

    # Variáveis de controle para rastrear em qual etapa a validação falhar
    tem_nivel = False
    tem_id_nivel = False

    try:
        # Acessa a estrutura de dicionários aninhados salvos no repositório do cache
        cache_metadados = cache.store["metadados_card-ogx"]["data"]

        # Percorre os blocos de configuração contidos no JSON retornado
        for item in cache_metadados:
            # Filtra apenas o bloco de chaves mapeado para a seletora de nível de atuação
            if item.get("external_id") == "qual-seu-nivel-de-atuacao":
                tem_nivel = True  # Encontrou o bloco de nível de atuação no cache

                # Itera sobre o array de opções ativas configuradas no Podio para este campo
                for opcao in item.get("options", []):
                    # Localiza o nó cujo identificador seja idêntico ao ID que estamos validando
                    if opcao.get("id") == id_nivel:
                        tem_id_nivel = True  # O ID enviado existe nas opções

                        # Realiza o isolamento de strings limpando lacunas de espaçamento antes da igualdade
                        if opcao.get("text", "").strip() == nome_nivel.strip():
                            return True  # Validação bem-sucedida: par ID e Nome é idêntico ao oficial

        # --- Retornos de erro exatos após sair de todos os loops ---
        if not tem_nivel:
            return "Não possui o extern_id qual-seu-nivel-de-atuacao"

        if not tem_id_nivel:
            return "ID do nível de atuação informado não foi encontrado nas opções"
        else:
            return "O nome do nível de atuação não corresponde ao ID informado"

    except (NameError, KeyError, TypeError):
        # Captura e neutraliza exceções de escopo ou de estrutura nula caso o cache não esteja carregado
        return "erro"


# =================================================================
# 3. ESTRUTURA DO MODELO (DTO)
# =================================================================

class NivelAtuacao(BaseModel):
    """
    Representa formalmente o Nível de Atuação dentro do ecossistema.

    Esta classe realiza validação cruzada tardia (`mode="after"`) garantindo que nenhuma entidade
    seja criada se o ID numérico e o Nome descritivo do nível não tiverem uma correspondência
    exata e idêntica na tabela de metadados ativa do cache do sistema.

    Attributes:
        id (PositiveInt): Código numérico indexador único que identifica o nível no Podio.
        nome (str): Nome do nível de atuação cadastrado no Podio (Ex: Estágio / Júnior).
    """

    # Configuração global do modelo no Pydantic v2
    model_config = ConfigDict(extra="ignore")

    # Código ID numérico único do nível de atuação cadastrado no Podio
    id: PositiveInt = Field(
        description="Id do nível de atuação no podio",
        json_schema_extra={"example": 15},
    )

    # Nome descritivo de exibição do nível de atuação no Podio
    nome: str = Field(
        description="nome do nível de atuação no podio",
        json_schema_extra={"example": "Estágio / Júnior"},
    )

    # =================================================================
    # 4. FUNÇÕES AUXILIARES / VALIDADORAS DE CAMPO
    # =================================================================

    @model_validator(mode="after")
    def verificar_nivel_atuacao_no_cache(self) -> Self | None:
        """
        Validador de negócio executado após a higienização que audita o nível de atuação em relação ao cache.

        Garante de forma cruzada que o ID informado exista no escopo correto e que o nome
        corresponda exatamente à opção cadastrada no cache de metadados do Podio.

        Returns:
            Self | None: Retorna a própria instância validada do modelo de NivelAtuacao.

        Raises:
            ValueError: Caso haja divergência cadastral entre o ID do nível e o nome informado.
        """
        # Encaminha as chaves consolidadas do modelo para auditoria contra os metadados ativos
        valido = validar_dados_nivel_atuacao(self.id, self.nome)

        if valido is True:
            return self

        # Comparação de erro idêntica caractere por caractere para levantar exceções de validação apropriadas
        if valido == "Não possui o extern_id qual-seu-nivel-de-atuacao":
            raise ValueError("Dados Inválidos: Não foi achada a referência de nível de atuação")

        elif valido == "ID do nível de atuação informado não foi encontrado nas opções":
            raise ValueError("Dados Inválidos: O id do nível de atuação informado não está presente nos dados")

        elif valido == "O nome do nível de atuação não corresponde ao ID informado":
            raise ValueError("Dados Inválidos: O nome do nível de atuação está incoerente")

        elif valido == "erro":
            raise ValueError("Metadados do Podio Não foram baixados")

        return None


# =================================================================
# 5. EXPORTAÇÃO CONSOLIDADA DO MÓDULO
# =================================================================

__all__ = ["NivelAtuacao"]