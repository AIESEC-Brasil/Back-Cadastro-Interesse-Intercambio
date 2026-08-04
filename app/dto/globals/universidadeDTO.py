"""Módulo de DTO e Validação de Universidade.

Integra as checagens do par ID e Nome da universidade informada com o cache
de metadados da aplicação, garantindo a integridade dos dados cadastrais.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from typing import Self, Union  # Type hints para referenciar a própria classe e tipos de união
from pydantic import (
    BaseModel,         # Classe base do Pydantic para declaração do DTO
    ConfigDict,        # Módulo de configuração de comportamento do modelo
    Field,             # Utilitário para definição de metadados e restrições nos campos
    PositiveInt,       # Validador nativo que aceita apenas números inteiros maiores que zero
    model_validator,   # Decorador para validadores de modelo completo (multi-campo)
)


# =================================================================
# 2. FUNÇÃO UTILITÁRIA DE VALIDAÇÃO CONTRA CACHE
# =================================================================

def validar_dados_universidade(nome: str, id: int) -> Union[bool, str]:
    """Valida se o ID e o Nome da universidade existem no cache e se pertencem ao mesmo registro.

    Args:
        nome (str): Nome da universidade informada no payload.
        id (int): ID da universidade informado no payload.

    Returns:
        Union[bool, str]: Retorna True em caso de sucesso, ou uma string descrevendo
        o motivo do erro para direcionamento de exceções.
    """
    # Lazy import do cache da aplicação para evitar dependências circulares durante a inicialização
    from app.cache import cache

    # Flags de controle para rastrear existência individual de cada parâmetro
    tem_id = False
    tem_nome = False

    try:
        # Acessa a lista de universidades armazenada na estrutura de cache em memória
        cache_universidades = cache.store["divisao-mercado-universidades"]["data"]

        # Iteração sobre a lista de instituições carregadas do banco
        for item in cache_universidades:
            item_id = item.get("id")
            item_nome = item.get("nome", "").strip()

            # Checa se o ID informado bate com o item atual
            if item_id == id:
                tem_id = True

            # Checa se o Nome informado bate com o item atual (case-insensitive)
            if item_nome.lower() == nome.strip().lower():
                tem_nome = True

            # Validação cruzada: se encontrou o ID correspondente, verifica o nome do mesmo item
            if item_id == id:
                if item_nome.lower() == nome.strip().lower():
                    # Sucesso: Tanto o ID quanto o Nome pertencem exatamente ao mesmo registro
                    return True
                if not tem_nome:
                    return "Nome da universidade não foi encontrado nas opções"
                else:
                    # Falha de divergência: O ID existe, mas o nome atribuído a ele é diferente
                    return "O nome da universidade não corresponde ao ID informado"

        # Tratamento de exceções de existência única se não houver retornado True no loop
        if not tem_id:
            return "ID da universidade não foi encontrado nas opções"

        return "Incoerência nos dados da universidade"

    except (NameError, KeyError, TypeError):
        # Trata falhas de parsing ou ausência da chave 'universidades' no cache
        return "erro"


# =================================================================
# 3. DTO PYDANTIC DE UNIVERSIDADE
# =================================================================

class Universidade(BaseModel):
    """Modelo Pydantic para representação e validação do objeto de Universidade."""

    # Configuração estrita: proíbe explicitamente campos extras não especificados no payload
    model_config = ConfigDict(extra="forbid")

    # Identificador numérico positivo da universidade (obrigatório)
    id: PositiveInt = Field(
        ...,
        description="ID identificador da instituição de ensino",
        json_schema_extra={"example": 102}
    )

    # Nome descritivo da universidade (obrigatório)
    nome: str = Field(
        ...,
        description="Nome completo da instituição de ensino",
        json_schema_extra={"example": "Universidade de São Paulo"}
    )

    @model_validator(mode="after")
    def verificar_universidade_no_cache(self) -> Self:
        """Validador Pydantic executado após a conversão de tipos básica dos campos.

        Executa a função de validação contra o cache e dispara exceções ValueError
        específicas de acordo com o retorno obtido.

        Raises:
            ValueError: Se o ID não existir, se o nome não existir ou se divergirem.

        Returns:
            Self: Retorna a própria instância validada caso passe em todas as regras.
        """
        # Executa a verificação cruzada contra o cache de metadados
        valido = validar_dados_universidade(nome=self.nome, id=self.id)

        # Se a validação retornar True, aprova a validação do modelo
        if valido is True:
            return self

        # Trata e converte cada tipo de falha retornada em ValueError amigável para a API
        if valido == "ID da universidade não foi encontrado nas opções":
            raise ValueError("Dados Inválidos: O ID da universidade informado não existe.")

        elif valido == "Nome da universidade não foi encontrado nas opções":
            raise ValueError("Dados Inválidos: O nome da universidade informado não existe.")

        elif valido == "O nome da universidade não corresponde ao ID informado":
            raise ValueError("Dados Inválidos: O nome e o ID informados pertencem a universidades diferentes.")

        elif valido == "erro":
            raise ValueError("Falha ao carregar metadados das universidades do cache.")

        # Lançamento genérico para prevenir incoerências não mapeadas
        raise ValueError("Dados Inválidos: Incoerência nos dados da universidade.")


# =================================================================
# 4. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["Universidade"]