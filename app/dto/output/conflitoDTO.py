"""Módulo para verificação e mapeamento de conflitos de dados de Leads.

Este módulo provê modelos Pydantic para estruturação do payload de saída e a
classe de serviço responsável por consultar o Podio para identificar e-mails ou
telefones já cadastrados no sistema.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import asyncio  # Módulo padrão do Python para gerenciamento de loops assíncronos e execução de Coroutines
from typing import (
    Any,       # Hint de tipo genérico/dinâmico para objetos que aceitam qualquer valor
    List,      # Hint de tipo para indicar coleções do tipo Lista de elementos
    Optional,  # Hint de tipo que indica que o atributo pode conter um valor ou ser Nulo (None)
)

from pydantic import (
    BaseModel,  # Classe base do Pydantic para criação, validação e estruturação automática de modelos
    Field,      # Função utilizada para mapear metadados dos atributos (descrição, exemplos, aliases)
    ConfigDict
)


# =================================================================
# 2. MODELOS DE SAÍDA (DTOS)
# =================================================================

class ConflitoEmail(BaseModel):
    """Modelo DTO representando um e-mail que gerou conflito de duplicidade.

    Attributes:
        email (str): Endereço de e-mail já cadastrado na plataforma.
    """

    # Endereço de e-mail identificado como duplicado na base de dados/Podio
    email: str = Field(
        description="Endereço de e-mail já existente no banco/Podio",
        json_schema_extra={"example": "usuario@exemplo.com"},
    )


class ConflitoTelefone(BaseModel):
    """Modelo DTO representando um telefone que gerou conflito de duplicidade.

    Attributes:
        numero (str): Número de telefone/celular já cadastrado na plataforma.
    """

    # Número de telefone/celular identificado como duplicado na base de dados/Podio
    numero: str = Field(
        alias="numero",
        description="Número de telefone/celular já existente no banco/Podio",
        json_schema_extra={"example": "11987654321"},
    )


class ConflitosLeadOutput(BaseModel):
    """Estrutura consolidada contendo todos os conflitos identificados para o Lead.

    Attributes:
        emails (Optional[List[ConflitoEmail]]): Lista de e-mails duplicados, ou None.
        telefone (Optional[List[ConflitoTelefone]]): Lista de telefones duplicados, ou None.
    """
    model_config = ConfigDict(extra="forbid")
    # Coleção de e-mails que apresentaram conflito durante a busca
    emails: Optional[List[ConflitoEmail]] = Field(
        default=None,
        description="Lista de e-mails em conflito com registros existentes",
    )

    # Coleção de telefones que apresentaram conflito durante a busca
    telefone: Optional[List[ConflitoTelefone]] = Field(
        default=None,
        description="Lista de números de telefone em conflito com registros existentes",
    )


# =================================================================
# 3. CLASSE DE SERVIÇO / REGRA DE NEGÓCIO
# =================================================================

class VerificadorConflitos:
    """Serviço responsável por validar duplicidade de dados do Lead no Podio."""

    def __init__(self, buscar_service: Any) -> None:
        """Inicializa a classe injetando a dependência do serviço de busca.

        Args:
            buscar_service (Any): Objeto/módulo responsável pelas consultas ao Podio (ex: BUSCAR).
        """
        # Injeção de dependência do serviço de busca do Podio
        self.buscar = buscar_service

    @validar
    async def _checar_emails(self, emails: list) -> List[ConflitoEmail]:
        """Realiza buscas assíncronas no Podio para validar lista de e-mails.

        Args:
            emails (list): Lista de objetos contendo a propriedade `.email`.

        Returns:
            List[ConflitoEmail]: Lista contendo os e-mails que já existem no sistema.
        """
        conflitos: List[ConflitoEmail] = []

        for e in emails:
            # Consulta o serviço externo buscando se o e-mail já está cadastrado
            resultado = await self.buscar.campo("email", e.email, True)

            # Se a busca retornar algum registro, mapeia o conflito
            if resultado:
                conflitos.append(ConflitoEmail(email=e.email))

        return conflitos

    @validar
    async def _checar_telefones(self, telefones: list) -> List[ConflitoTelefone]:
        """Realiza buscas assíncronas no Podio para validar lista de telefones.

        Args:
            telefones (list): Lista de objetos contendo a propriedade `.numero`.

        Returns:
            List[ConflitoTelefone]: Lista contendo os números que já existem no sistema.
        """
        conflitos: List[ConflitoTelefone] = []

        for t in telefones:
            # Consulta o serviço externo buscando se o número já está cadastrado
            resultado = await self.buscar.telefone(t.numero)

            # Se a busca retornar algum registro, mapeia o conflito
            if resultado:
                conflitos.append(ConflitoTelefone(numero=t.numero))

        return conflitos

    @validar
    def executar(self, lead_input: Any) -> dict[str, list[ConflitoEmail] | None | list[ConflitoTelefone]] | None:
        """Executa a verificação completa de e-mails e telefones de um lead.

        Extrai as coleções de e-mail e telefone do objeto de entrada, roda o loop
        de eventos assíncrono para validação no Podio e consolida os resultados.

        Args:
            lead_input (Any): Objeto DTO contendo os dados de entrada do Lead (.email e .telefone).

        Returns:
            Optional[ConflitosLeadOutput]: Objeto Pydantic com os conflitos mapeados
                                           ou None caso nenhum conflito seja encontrado.
        """
        # Extrai com segurança as listas de email e telefone do DTO de entrada
        lista_emails = getattr(lead_input, "email", [])
        lista_telefones = getattr(lead_input, "telefone", [])

        # Dispara as rotinas assíncronas de verificação
        emails_conflito = asyncio.run(self._checar_emails(lista_emails))
        telefones_conflito = asyncio.run(self._checar_telefones(lista_telefones))

        # Se houver qualquer conflito (de e-mail ou telefone), instancia e retorna o modelo
        if emails_conflito or telefones_conflito:
            return {
                    "emails":emails_conflito or None,
                    "telefone":telefones_conflito or None,
                }

        # Se nenhum conflito for identificado, retorna None (Lead está limpo)
        return None


# =================================================================
# 4. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["VerificadorConflitos", "ConflitosLeadOutput"]