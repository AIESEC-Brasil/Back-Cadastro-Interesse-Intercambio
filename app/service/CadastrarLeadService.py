"""
Serviço de cadastro, pré-registro e qualificação de leads.

Este módulo orquestra a checagem de duplicidade, verificação de conflitos,
criação, atualização e qualificação complementar (com upload de arquivos)
de registros de leads integrados com a API do Podio.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import asyncio  # Utilitário para executar corrotinas assíncronas em contexto síncrono
import logging  # Módulo nativo de logging para emissão de logs e diagnósticos
from typing import Any, Dict, Tuple, Union  # Anotações de tipo estático para compatibilidade

# Módulos internos: Clientes HTTP e de busca
from ..clients import Buscar

# Módulos internos: Abstração de regras e comunicação com Podio
from ..classe import LeadPodio

# Módulos internos: Configurações globais da aplicação
from ..config import APP_ID

# Módulos internos: Data Transfer Objects (DTOs) e Enums HTTP
from ..dto import (
    ConflitosLeadOutput,
    CriarPreCadastroLead,
    HttpStatus,
    QualificacaoLead,
    RetornoGenerico,
    VerificadorConflitos,
)

# Instancia o logger específico deste módulo
logger = logging.getLogger(__name__)


# =================================================================
# 2. LÓGICA DE NEGÓCIO / SERVIÇO
# =================================================================

@validar
def cadastrar_lead(
        lead_input: CriarPreCadastroLead,
) -> tuple[dict[Any, Any], HttpStatus] | tuple[Any, HttpStatus] | dict[str, Any]:
    """Realiza o pré-cadastro de um lead com checagem assíncrona de conflitos e duplicidades.

    O fluxo executa três verificações principais:
    1. Consulta se o lead já possui cadastro completo no sistema.
    2. Se existir, atualiza suas informações e retorna HTTP 200 OK.
    3. Se não existir, verifica possíveis conflitos (ex: e-mail ou telefone duplicados).
       Em caso de conflito, retorna a estrutura `RetornoGenerico` com HTTP 409 CONFLICT.
    4. Não havendo conflitos, conclui o cadastro no Podio e retorna HTTP 201 CREATED.

    Args:
        lead_input (CriarPreCadastroLead): DTO contendo os dados de entrada do lead
            para criação ou atualização.

    Returns:
        tuple[dict[Any, Any], HttpStatus] | tuple[Any, HttpStatus] | dict[str, Any]:
            Uma tupla contendo o payload de resposta (ou dicionário serializado) e o
            código de status HTTP correspondente:
            - (dict, HttpStatus.OK): Lead existente atualizado com sucesso.
            - (dict, HttpStatus.CONFLICT): Conflito ou duplicidade identificada no cadastro.
            - (dict / tuple, HttpStatus.CREATED): Novo lead cadastrado com sucesso.
    """
    logger.info("Iniciando fluxo de cadastro/pré-registro para o lead.")

    # Instancia o cliente de busca de itens filtrando pelo APP_ID global
    buscar_client = Buscar(APP_ID)

    # Instancia o serviço responsável por operações de gravação e atualização no Podio
    lead_ogx: LeadPodio = LeadPodio(APP_ID)

    # Executa a busca assíncrona para checar se o lead já existe na base
    logger.info("Consultando se o lead já possui registro na base...")
    lead_existe = asyncio.run(
        buscar_client.item_completo(lead_input.model_dump())
    )

    # Se o lead já existir na base de dados, atualiza seus registros e retorna HTTP 200 OK
    if lead_existe:
        logger.info("Lead já cadastrado encontrado na base. Executando atualização de dados...")
        resultado_atualizacao = lead_ogx.atualizar_lead(lead_existe, lead_input)
        logger.info("Lead atualizado com sucesso (HTTP 200 OK).")
        return resultado_atualizacao

    # Inicializa o serviço de verificação de inconsistências e duplicidades
    logger.info("Lead não localizado. Iniciando checagem de conflitos e inconsistências...")
    verificador = VerificadorConflitos(buscar_client)

    # Executa a regra de validação de conflitos de cadastro
    conflitos = verificador.executar(lead_input)

    # Se houverem conflitos, estrutura a resposta padronizada e retorna HTTP 409 CONFLICT
    if conflitos:
        logger.warning(
            "Conflito ou duplicidade identificada durante a verificação de cadastro (HTTP 409 CONFLICT)."
        )
        return conflitos, HttpStatus.CONFLICT

    # Sem conflitos identificados: realiza a criação do novo lead (HTTP 201 CREATED)
    logger.info("Nenhum conflito encontrado. Cadastrando novo lead no Podio (HTTP 201 CREATED)...")
    return lead_ogx.cadastrar_lead(lead_input)


@validar
def qualificar_lead(
        lead_input: QualificacaoLead,
) -> tuple[dict[Any, Any], HttpStatus] | tuple[Any, HttpStatus] | dict[str, Any]:
    """Realiza a qualificação complementar de um lead existente no Podio.

    Atualiza o card do lead com os dados acadêmicos/profissionais e, caso um
    currículo (PDF em Base64) tenha sido enviado, executa o upload e o anexo do arquivo.

    Args:
        lead_input (QualificacaoLead): DTO contendo os dados de qualificação
            e opcionalmente o arquivo de currículo.

    Returns:
        tuple[dict[Any, Any], HttpStatus] | tuple[Any, HttpStatus] | dict[str, Any]:
            Uma tupla contendo o payload de resposta atualizado e o status HTTP correspondente:
            - (dict, HttpStatus.OK): Qualificação e anexo processados com sucesso.
            - (dict, HttpStatus.BAD_REQUEST): Falha na validação ou parâmetros do lead.
    """
    logger.info("Iniciando fluxo de qualificação complementar para o lead.")

    # Instancia o serviço responsável por operações de gravação e atualização no Podio
    lead_ogx: LeadPodio = LeadPodio(APP_ID)

    # Executa a atualização dos dados e o upload/anexo do currículo no Podio
    return lead_ogx.qualificar_lead(lead_input)


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = [
    "cadastrar_lead",
    "qualificar_lead",
]