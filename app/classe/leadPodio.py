"""Módulo de abstração e gerenciamento de operações de Leads no Podio."""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import asyncio  # Execução de corrotinas assíncronas em contexto síncrono
import logging  # Módulo nativo de logging para rastreamento e diagnósticos
from types import CoroutineType  # Importa o tipo CoroutineType para tipagem de funções assíncronas
from typing import Any  # Importa Any para tipagens dinâmicas e flexíveis

# Importa PositiveInt do Pydantic para garantir que identificadores numéricos sejam inteiros positivos
from pydantic import PositiveInt

from app.helper import (
    payload_atualizar_existe,
    payload_expa,
    payload_pre_cadastro_podio,
    payload_qualificacao_lead,
)

# Importa as funções de comunicação externa com a API do Podio
from ..clients import (
    adicionar_lead,
    atualizar_lead,
    remover_lead,
    upload_e_anexar_curriculo,
)

# Importa os modelos de DTO de entrada e saída para validação estrutural do lead
from ..dto import (
    CriarPreCadastroLead,
    HttpStatus,
    LeadPreCadastroInput,
    LeadPreCadastroOutput,
    QualificacaoLead,
)

# Instancia o logger específico deste módulo
logger = logging.getLogger(__name__)


# =================================================================
# 2. CLASSE DE SERVIÇO / ADAPTADOR PODIO
# =================================================================

class LeadPodio:
    """Classe de serviço responsável por gerenciar operações de Leads no Podio.

    Esta classe encapsula a lógica de integração com a API do Podio para cadastro,
    atualização, qualificação (com upload de arquivos) e remoção de registros de leads,
    aplicando validações estruturais por meio do decorador `@validar` e tipagens estritas.

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
        logger.debug("Instância de LeadPodio inicializada com app_id: %s", self.app_id)

    @validar
    def cadastrar_lead(
            self, lead: CriarPreCadastroLead
    ) -> tuple[Any, HttpStatus] | dict[str, Any]:
        """Realiza o cadastro de um novo lead de forma assíncrona na plataforma Podio.

        Utiliza os dados validados do payload de entrada e o `app_id` configurado
        na instância para efetuar a requisição de inserção externa.

        Args:
            lead (CriarPreCadastroLead): Objeto contendo os dados estruturados e
                validados do pré-cadastro do lead.

        Returns:
            tuple[Any, HttpStatus] | dict[str, Any]: Estrutura com os dados processados
                e o código de status HTTP correspondente.
        """
        logger.debug(
            "LeadPodio.cadastrar_lead acionado. Disparando asyncio.run(adicionar_lead) para app_id=%s...",
            self.app_id
        )
        return asyncio.run(adicionar_lead(
            chave="ogx-token-podio",
            payload=payload_pre_cadastro_podio(lead),
            response_dto=lead.model_dump(exclude_none=True),
            payload_expa=payload_expa(lead),
            app_id=self.app_id,
        ))

    @staticmethod
    @validar
    def atualizar_lead(
            lead_existe: dict[str, Any], lead: CriarPreCadastroLead | QualificacaoLead
    ) -> tuple[Any, HttpStatus] | dict[str, Any]:
        """Atualiza os dados de um lead já existente com base nas informações fornecidas.

        Args:
            lead_existe (dict[str, Any]): Dicionário contendo os dados atuais do
                registro recuperado previamente do sistema/Podio.
            lead (CriarPreCadastroLead): Objeto de entrada contendo as novas
                informações validadas para atualização.

        Returns:
            tuple[Any, HttpStatus] | dict[str, Any]: Dicionário/Estrutura contendo os
                dados consolidados da atualização.
        """
        logger.debug("LeadPodio.atualizar_lead acionado. Disparando asyncio.run(atualizar_lead)...")
        return asyncio.run(atualizar_lead(
            chave="ogx-token-podio",
            payload=payload_atualizar_existe(lead),
            response_dto=lead.model_dump(exclude_none=True),
            data_response=lead_existe
        ))

    @staticmethod
    @validar
    def qualificar_lead(
            lead: QualificacaoLead
    ) -> tuple[Any, HttpStatus] | dict[str, Any]:
        """Executa o processo de qualificação complementar do lead no Podio.

        Realiza a atualização dos campos acadêmicos/profissionais e, caso um arquivo de
        currículo tenha sido fornecido em `lead.curriculo`, dispara o upload e anexo do PDF.

        Args:
            lead (QualificacaoLead): DTO de qualificação contendo as informações complementares
                do lead e opcionalmente o arquivo PDF em Base64.

        Returns:
            tuple[Any, HttpStatus] | dict[str, Any]: Estrutura com os dados consolidados e
                o status HTTP correspondente à operação.
        """
        logger.debug("LeadPodio.qualificar_lead acionado. Atualizando campos de qualificação...")

        # 1. Atualização dos campos de qualificação no card do Podio
        data_response = {"item_id": lead.item_id}
        resultado_atualizacao, status = asyncio.run(atualizar_lead(
            chave="ogx-token-podio",
            payload=payload_qualificacao_lead(lead),
            response_dto=lead.model_dump(exclude_none=True),
            data_response=lead.model_dump(exclude_none=True),
            atualizar="qualificação"
        ))

        # Se a atualização falhar, interrompe e retorna a resposta de erro
        if not 200 <= status.value <= 399:
            logger.error("Falha ao qualificar os campos do lead no Podio (Status: %s).", status)
            return resultado_atualizacao, status

        # 2. Upload e anexo do currículo em PDF (se houver currículo no DTO)
        if lead.curriculo:
            logger.debug("Currículo identificado. Disparando upload_e_anexar_curriculo...")
            response_dto = resultado_atualizacao if isinstance(resultado_atualizacao, dict) else lead.model_dump(exclude_none=True)

            return asyncio.run(upload_e_anexar_curriculo(
                chave="ogx-token-podio",
                data=lead,
                response_dto=response_dto
            ))

        return resultado_atualizacao, status

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
        logger.warning(
            "LeadPodio.remover_lead foi chamado, mas a integração com a API remota ainda é um stub."
        )
        return lead


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["LeadPodio"]