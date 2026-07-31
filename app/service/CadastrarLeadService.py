"""Serviço de cadastro e pré-registro de leads.

Este módulo orquestra a checagem de duplicidade, verificação de conflitos
e criação de novos registros de leads integrados com serviços externos.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import asyncio  # Execução de corrotinas assíncronas em contexto síncrono
from typing import Dict, Tuple, Union  # Anotações de tipo estático

from flask import Response, jsonify  # Objetos e utilitários HTTP do Flask

# Importações dos DTOs e utilitários internos
from app.clients import buscar_id_card
from ..clients import Buscar
from ..config import APP_ID
from ..dto import (
    CriarPreCadastroLead,
    HttpStatus,
    LeadPreCadastroOutput,
    VerificadorConflitos,
)


# =================================================================
# 2. LÓGICA DE NEGÓCIO / SERVIÇO
# =================================================================

@validar
def cadastrar_lead(
        lead_input: CriarPreCadastroLead,
) -> Union[
    Tuple[Dict[str, str], int],
    Tuple[Response, HttpStatus],
    Tuple[LeadPreCadastroOutput, int],
]:
    """Realiza o pré-cadastro de um lead com checagem assíncrona de conflitos.

    Args:
        lead_input (CriarPreCadastroLead): DTO contendo os dados do lead.

    Returns:
        Union[Tuple[Dict[str, str], int], Tuple[Response, HttpStatus], Tuple[LeadPreCadastroOutput, int]]:
            Retorna o dicionário serializado do lead com o ID do card e o código HTTP apropriado
            (200 OK para existente, 409 CONFLICT para conflito, 201 CREATED para novo registro).
    """
    # Instancia o cliente de busca de itens com o App ID global
    buscar_client = Buscar(APP_ID)

    # Executa a busca assíncrona para checar se o lead já possui cadastro completo
    lead_existe = asyncio.run(
        buscar_client.item_completo(lead_input.model_dump())
    )

    # Se o lead já existir na base, recupera o ID do card e retorna status 200 OK
    if lead_existe:
        data = lead_input.model_dump()
        data["item_id"] = buscar_id_card(lead_existe)
        return data, 200

    # Inicializa o verificador de conflitos de cadastro
    verificador = VerificadorConflitos(buscar_client)

    # Executa a validação de inconsistências/duplicidades
    conflitos = verificador.executar(lead_input)

    # Se forem detectados conflitos, retorna os detalhes com HTTP 409 CONFLICT
    if conflitos:
        return conflitos.model_dump(exclude_none=True), HttpStatus.CONFLICT

    # Conclui o cadastro gerando os dados do novo lead (HTTP 201 CREATED)
    data = lead_input.model_dump()
    data["item_id"] = 243426
    return data, 201


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["cadastrar_lead"]