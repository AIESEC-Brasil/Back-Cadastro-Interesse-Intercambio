import asyncio  # Execução de corrotinas assíncronas em contexto síncrono

# Importa o tipo CoroutineType do módulo nativo types para tipagem de funções assíncronas
from types import CoroutineType
# Importa Any do módulo typing para permitir tipagens dinâmicas e flexíveis
from typing import Any

# Importa PositiveInt do Pydantic para garantir que identificadores numéricos sejam estritamente inteiros positivos (> 0)
from pydantic import PositiveInt

# Importa os modelos de DTO (Data Transfer Objects) de entrada e saída para validação estrutural do lead
from ..dto import LeadPreCadastroInput, LeadPreCadastroOutput,CriarPreCadastroLead

# Importa as funções de comunicação externa com a API do Podio para adicionar, atualizar e remover registros
from ..clients import adicionar_lead, atualizar_lead, remover_lead


class LeadPodio:
    """Classe de serviço responsável por gerenciar operações de Leads no Podio.

    Esta classe encapsula a lógica de integração com a API do Podio para cadastro,
    atualização e remoção de registros de leads, aplicando validações estruturais
    por meio do decorador `@validar` e tipagens estritas.

    Attributes:
        app_id (PositiveInt): Identificador numérico do aplicativo/espaço no Podio
            utilizado como alvo para a criação de novos registros. Padrão: 0.
    """

    @validar
    def __init__(self, app_id: PositiveInt = 0) -> None:
        """Inicializa a instância de gerenciamento do Lead no Podio.

        Args:
            app_id (PositiveInt, optional): ID do aplicativo no Podio onde as
                operações de inserção serão direcionadas. Padrão é 0.
        """
        self.app_id = app_id

    @validar
    def cadastrar_lead(
            self, lead: CriarPreCadastroLead
    ) -> tuple[dict[Any, Any], int]:
        """Realiza o cadastro de um novo lead de forma assíncrona na plataforma Podio.

        Utiliza os dados validados do payload de entrada e o `app_id` configurado
        na instância para efetuar a requisição de inserção externa.

        Args:
            lead (LeadPreCadastroInput): Objeto contendo os dados estruturados e
                validados do pré-cadastro do lead.

        Returns:
            CoroutineType[Any, Any, tuple[dict[Any, Any], int]]: Uma corrotina que,
                ao ser resolvida, retorna uma tupla contendo o dicionário com a
                resposta dos dados do Podio e o respectivo código de status HTTP.
        """
        return asyncio.run(adicionar_lead(
            chave="ogx-token-podio",
            payload=lead.model_dump(exclude_none=True),
            app_id=self.app_id,
        ))

    @staticmethod
    @validar
    def atualizar_lead(
            lead_existe: dict[str, Any], lead: CriarPreCadastroLead
    ) -> dict[Any, Any]:
        """Atualiza os dados de um lead já existente com base nas informações fornecidas.

        Args:
            lead_existe (dict[str, Any]): Dicionário contendo os dados atuais do
                registro recuperado previamente do sistema/Podio.
            lead (LeadPreCadastroInput): Objeto de entrada contendo as novas
                informações validadas para atualização.

        Returns:
            LeadPreCadastroOutput: Objeto de saída estruturado contendo os dados
                consolidados da atualização.
        """
        return asyncio.run(atualizar_lead(
            chave="ogx-token-podio",
            payload=lead.model_dump(exclude_none=True),
            data_response=lead_existe
    ))

    @staticmethod
    @validar
    def remover_lead(
            lead_existe: dict[str, Any], lead: LeadPreCadastroInput
    ) -> LeadPreCadastroOutput:
        """Executa a remoção (ou inativação) de um lead cadastrado.

        Args:
            lead_existe (dict[str, Any]): Dicionário contendo os dados do
                registro existente que será alvo da remoção.
            lead (LeadPreCadastroInput): Objeto de entrada contendo os dados
                de suporte associados à operação de remoção.

        Returns:
            LeadPreCadastroOutput: Objeto estruturado de saída confirmando os
                dados associados ao processo de remoção.
        """
        return lead

__all__ = ["LeadPodio"]