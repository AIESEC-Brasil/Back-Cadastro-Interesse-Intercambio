"""Endpoint de metadados do formulário B2C."""

import logging
from datetime import datetime
from typing import Any, Self
from zoneinfo import ZoneInfo

from asgiref.sync import async_to_sync
from flask_openapi3 import APIView, Tag
from pydantic import ValidationError

from ..cache import cache
from ..clients.b2c import enviar_metadados_b2c
from ..clients.expa import enviar_payload_expa
from ..dto.exception import ValidationErrorResponse
from ..dto.input import CriarPreCadastroLead, QualificacaoLead
from ..dto.output import HttpStatus, LeadPreCadastroOutput, Metadados
from ..dto.persistence import LeadPersistencia
from ..router import Router
from ..utils.payload import montar_dto_persistencia, montar_payload_expa

new_lead_ogx: Router = Router(name="cadatro_interesse_intercambio", url_prefix="/new-lead-ogx")
logger: logging.Logger = logging.getLogger(__name__)

# ==============================================================================
# DOCUMENTAÇÃO DA ROTA DE METADADOS
# ==============================================================================
METADADOS_DESCRIPTION: str = """\
Usa o cache válido ou consulta a origem \
quando ele está ausente ou expirado. Preserva todos os campos do Apps Script \
e remove opções explicitamente inativas.

A resposta contém `data.fields`, com os campos do formulário B2C, e \
`timestamp`, com a última atualização do cache no fuso de São Paulo."""

METADADOS_RESPONSES: dict[int | str, Any] = {
    200: Metadados,
    422: ValidationErrorResponse,
    502: {
        "description": "A origem falhou ou devolveu um payload inválido.",
        "content": {"text/html": {"schema": {"type": "string"}}},
    },
    504: {
        "description": "A consulta à origem excedeu o tempo limite.",
        "content": {"text/html": {"schema": {"type": "string"}}},
    },
    "default": {
        "description": "Outros erros HTTP são exibidos na página genérica de erro.",
        "content": {"text/html": {"schema": {"type": "string"}}},
    },
}

# ==============================================================================
# ROTA DE CONSULTA DOS METADADOS B2C
# ==============================================================================
@new_lead_ogx.get(
    "/metadados",
    summary="Consultar metadados do Banco para formulário B2C",
    tags=[Tag(name="Metadados")],
    description=METADADOS_DESCRIPTION,
    responses=METADADOS_RESPONSES,
)
def buscar_metadados() -> tuple[dict[str, Any], int]:
    """Busca os metadados do formulário B2C para a rota `/new-lead-ogx/metadados`."""
    logger.info("Requisição recebida para buscar metadados B2C")
    payload: Any
    status: int
    payload, status = async_to_sync(cache.get_or_set)(
        key="metadados_b2c",
        fetch=enviar_metadados_b2c,
        baixando="Metadados B2C",
    )
    if status < 200 or status >= 300:
        try:
            status_name: str = HttpStatus(status).name
        except ValueError:
            status_name = "UNKNOWN"
        logger.error(
            "Falha ao buscar metadados B2C | HTTP %s %s", status, status_name
        )
        return payload, status
    else:
        logger.info("Metadados B2C retornados com sucesso")

    cache_entry: dict[str, Any] | None = cache.store.get("metadados_b2c")
    if cache_entry is None:
        logger.error(
            "Metadados B2C não foram armazenados no cache | HTTP %s %s",
            HttpStatus.BAD_GATEWAY.value,
            HttpStatus.BAD_GATEWAY.name,
        )
        return {"error": "Metadados B2C indisponíveis."}, HttpStatus.BAD_GATEWAY

    timestamp: datetime = datetime.fromtimestamp(
        cache_entry["timestamp"], ZoneInfo("America/Sao_Paulo")
    )
    metadata: dict[str, Any] = {**payload, "timestamp": timestamp}
    return metadata, status

# ==============================================================================
# DOCUMENTAÇÃO DAS OPERAÇÕES DE CADASTRO
# ==============================================================================
CADASTRO_POST_DESCRIPTION: str = """\
Recebe os dados da primeira etapa, cria o lead no EXPA e retorna o DTO de
persistência com o `id` (`person_id`) retornado pelo EXPA e status
`pré-cadastro`. A senha não é devolvida."""

CADASTRO_PUT_DESCRIPTION: str = """\
Recebe os dados complementares da segunda etapa e atualiza o lead criado no
pré-cadastro. A implementação da atualização ainda está pendente."""

CADASTRO_POST_RESPONSES: dict[int | str, Any] = {
    201: LeadPersistencia,
    502: {
        "description": "A resposta de criação do EXPA é inválida ou incompleta.",
        "content": {"application/json": {"schema": {"type": "object"}}},
    },
    422: ValidationErrorResponse,
    "default": {
        "description": "Erro HTTP exibido na página genérica de erro.",
        "content": {"text/html": {"schema": {"type": "string"}}},
    },
}

CADASTRO_PUT_RESPONSES: dict[int | str, Any] = {
    501: {
        "description": "A atualização do cadastro ainda não está implementada.",
        "content": {"text/html": {"schema": {"type": "string"}}},
    },
    422: ValidationErrorResponse,
    "default": {
        "description": "Erro HTTP exibido na página genérica de erro.",
        "content": {"text/html": {"schema": {"type": "string"}}},
    },
}


# ==============================================================================
# VIEW DE CADASTRO DE LEADS
# ==============================================================================
cadastro_lead_view: APIView = APIView(
    view_tags=[Tag(name="New Lead OGX")],
    url_prefix=new_lead_ogx.url_prefix,
)


@cadastro_lead_view.route("/cadastro")
class CadastroLeadView:
    """Agrupa a criação e a atualização do cadastro de leads."""

    @cadastro_lead_view.doc(
        summary="Criar pré-cadastro de lead",
        description=CADASTRO_POST_DESCRIPTION,
        responses=CADASTRO_POST_RESPONSES,
    )
    def post(
        self: Self, body: CriarPreCadastroLead
    ) -> tuple[LeadPersistencia | dict[str, str], int]:
        """Cria o lead no EXPA e retorna os dados para persistência."""
        payload: Any = montar_payload_expa(body)
        status: int
        resposta: Any
        status, resposta = async_to_sync(enviar_payload_expa)(payload)

        if not 200 <= status < 300:
            status_erro: int = status if 400 <= status < 600 else HttpStatus.BAD_GATEWAY
            logger.error("Falha na criação do lead no EXPA | HTTP %s", status)
            mensagem: str = (
                resposta.get("erro", resposta.get("error", "Falha ao criar lead no EXPA."))
                if isinstance(resposta, dict)
                else "Falha ao criar lead no EXPA."
            )
            return {"error": str(mensagem)}, status_erro

        if not isinstance(resposta, dict) or resposta.get("sucesso") is not True:
            status_expa: Any = (
                resposta.get("status_code") if isinstance(resposta, dict) else None
            )
            if (
                not isinstance(status_expa, int)
                or isinstance(status_expa, bool)
                or not 400 <= status_expa < 600
            ):
                status_expa = HttpStatus.BAD_GATEWAY
            mensagem = (
                resposta.get("erro", resposta.get("mensagem", "O EXPA não confirmou a criação."))
                if isinstance(resposta, dict)
                else "Resposta inválida do EXPA."
            )
            logger.error(
                "EXPA não confirmou a criação do lead | HTTP %s",
                status_expa,
            )
            return {"error": str(mensagem)}, int(status_expa)

        person_id: Any = resposta.get("person_id")
        if (
            not isinstance(person_id, (str, int))
            or isinstance(person_id, bool)
            or not str(person_id).isdigit()
            or int(person_id) <= 0
        ):
            logger.error("EXPA confirmou criação sem retornar person_id válido")
            return (
                {"error": "Resposta do EXPA sem person_id válido."},
                HttpStatus.BAD_GATEWAY,
            )

        dados_saida: dict[str, Any] = body.model_dump(
            mode="json",
            exclude={"senha"},
        )
        dados_saida["id"] = int(person_id)
        try:
            lead_criado = LeadPreCadastroOutput.model_validate(dados_saida)
            lead_persistencia = montar_dto_persistencia(body, lead_criado)
        except ValidationError:
            logger.exception("Não foi possível montar a resposta do lead criado")
            return (
                {"error": "Não foi possível montar a resposta do lead criado."},
                HttpStatus.INTERNAL_SERVER_ERROR,
            )
        return lead_persistencia, HttpStatus.CREATED

    @cadastro_lead_view.doc(
        summary="Atualizar cadastro do lead",
        description=CADASTRO_PUT_DESCRIPTION,
        responses=CADASTRO_PUT_RESPONSES,
    )
    def put(
        self: Self, body: QualificacaoLead
    ) -> tuple[dict[str, str], int]:
        """Recebe dados complementares da segunda etapa do cadastro."""
        return (
            {"error": "A atualização do cadastro ainda não está implementada."},
            int(HttpStatus.NOT_IMPLEMENTED),
        )


__all__ = ["cadastro_lead_view", "new_lead_ogx"]
