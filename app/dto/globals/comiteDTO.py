"""Módulo de DTO para Estrutura de Comitê Local (AIESEC).

Este módulo define o modelo Pydantic `Comite` e a função de validação cruzada
`validar_dados_comite`, responsáveis por auditar se o ID e o nome da unidade local
informados na requisição coincidem com os metadados ativos armazenados no cache do sistema.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from typing import (
    Self,   # Hint de tipo para indicar que o método retorna a própria instância da classe.
    Union,  # Hint de tipo para declarar que uma função aceita ou retorna mais de um tipo de dado.
)

from pydantic import (
    BaseModel,        # Classe base para criação de modelos de dados com validação automática.
    ConfigDict,       # Objeto de configuração para definir comportamentos do modelo (ex: proibir campos extras).
    Field,            # Utilizado para definir metadados dos campos, como descrições, aliases e exemplos para o JSON Schema.
    model_validator,  # Decorador para aplicar regras de validação no nível do modelo completo (múltiplos campos).
)


# =================================================================
# 2. FUNÇÃO DE VALIDAÇÃO DE NEGÓCIO (CACHE METADADOS)
# =================================================================

def validar_dados_comite(id_comite: int, nome_comite: str) -> Union[bool, str]:
    """Varre a base de dados do cache local de metadados para confirmar a integridade de um comitê.

    Verifica de forma cruzada se o ID informado existe dentro do escopo do campo 'aiesec-mais-proxima'
    e se o nome correspondente naquele nó de dados é equivalente ao nome enviado pelo payload da API.

    Args:
        id_comite (int): Identificador numérico inteiro que descreve a unidade local.
        nome_comite (str): Nome descritivo da unidade fornecido pelo usuário ou formulário.

    Returns:
        Union[bool, str]: True se o ID e o Nome coincidirem com os registros do cache;
                          String com a mensagem exata do erro caso contrário.
    """
    # Importação tardia (lazy import) do objeto de cache global para evitar importação circular
    from app.cache import cache

    # Variáveis de controle para rastrear em qual etapa a validação falhar
    tem_comite = False
    tem_id_comite = False

    try:
        # Acessa a estrutura de dicionários aninhados salvos no repositório do cache
        cache_metadados = cache.store["metadados_card-ogx"]["data"]

        # Percorre os blocos de configuração contidos no JSON retornado
        for item in cache_metadados:
            # Filtra apenas o bloco de chaves mapeado para a seletora de comitês locais da AIESEC
            if item.get("external_id") == "aiesec-mais-proxima":
                tem_comite = True  # Encontrou o bloco do comitê no cache

                # Itera sobre o array de opções ativas configuradas no Podio para este campo
                for opcao in item.get("options", []):
                    # Localiza o nó cujo identificador seja idêntico ao ID que estamos validando
                    if opcao.get("id") == id_comite:
                        tem_id_comite = True  # O ID enviado existe nas opções

                        # Realiza o isolamento de strings limpando lacunas de espaçamento antes da igualdade
                        if opcao.get("text", "").strip() == nome_comite.strip():
                            return True  # Validação bem-sucedida: par ID e Nome é idêntico ao oficial

        # --- Retornos de erro exatos após sair de todos os loops ---
        if not tem_comite:
            return "Não possui o extern_id aiesec-mais-proxima"

        if not tem_id_comite:
            return "ID do comitê informado não foi encontrado nas opções"
        else:
            return "O nome do comitê não corresponde ao ID informado"

    except (NameError, KeyError, TypeError):
        # Captura e neutraliza exceções de escopo ou de estrutura nula caso o cache não esteja carregado
        return "erro"


# =================================================================
# 3. MODELO DE DADOS (DTO)
# =================================================================

class Comite(BaseModel):
    """Representa formalmente um Comitê Local (Unidade operacional da AIESEC) dentro do ecossistema.

    Esta classe realiza validação cruzada tardia (`mode="after"`) garantindo que nenhuma entidade
    seja criada se o ID numérico local e o Nome descritivo da filial não tiverem uma correspondência
    exata e idêntica na tabela de metadados ativa do cache do sistema.

    Attributes:
        id (int): Código numérico indexador único que identifica o comitê local.
        nome (str): Nome amigável de exibição da praça regional da unidade (Ex: Recife(PE)).
    """

    # Configuração global do modelo no Pydantic v2
    model_config = ConfigDict(
        extra="forbid"  # Rejeita estritamente campos extras não declarados no payload para maior segurança
    )

    # Código ID numérico único do comitê local cadastrado no Podio
    id: int = Field(
        description="ID interno numérico da entidade",
        json_schema_extra={"example": 32},
    )

    # Nome descritivo de exibição da unidade do comitê local
    nome: str = Field(
        description="Nome amigável da unidade (Comitê Local)",
        json_schema_extra={"example": "Recife(PE)"},
    )

    @model_validator(mode="after")
    def verificar_comite_no_cache(self) -> Self | None:
        """Validador de negócio executado após a higienização que audita o comitê em relação ao cache.

        Garante de forma cruzada que o ID informado exista no escopo correto e que o nome
        corresponda exatamente à unidade cadastrada no cache de metadados do Podio.

        Returns:
            Self | None: Retorna a própria instância validada do modelo de Comitê.

        Raises:
            ValueError: Caso haja divergência cadastral entre o ID do comitê e o nome informado.
        """
        # Encaminha as chaves consolidadas do modelo para auditoria contra os metadados ativos
        valido = validar_dados_comite(self.id, self.nome)

        if valido is True:
            return self

        # Comparação de erro idêntica caractere por caractere para levantar exceções de validação apropriadas
        if valido == "Não possui o extern_id aiesec-mais-proxima":
            raise ValueError("Dados Inválidos: Não foi achada a referência de comitê local")

        elif valido == "ID do comitê informado não foi encontrado nas opções":
            raise ValueError("Dados Inválidos: O id do comitê informado não está presente nos dados")

        elif valido == "O nome do comitê não corresponde ao ID informado":
            raise ValueError("Dados Inválidos: O nome do comitê está incoerente")

        elif valido == "erro":
            raise ValueError("Metadados do Podio Não foram baixados")

        return None


# =================================================================
# 4. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["Comite"]