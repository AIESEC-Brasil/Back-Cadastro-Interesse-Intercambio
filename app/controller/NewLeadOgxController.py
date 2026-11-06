"""Endpoint de metadados do formulário B2C."""

import logging
from datetime import datetime
from typing import Any, Self
from zoneinfo import ZoneInfo

from asgiref.sync import async_to_sync
from flask_openapi3 import APIView, Tag
from pydantic import ValidationError

from ..cache import cache
from ..clients.b2c import (
    enviar_lead_b2c,
    enviar_metadados_b2c,
    validar_link_conclusao_b2c,
)
from ..clients.expa import enviar_payload_expa
from ..core.logger import log_resposta_externa
from ..dto.exception import BaseErrorResponse, ValidationErrorResponse
from ..dto.input import (
    CompletarCadastroB2C,
    CriarPreCadastroB2C,
    CriarPreCadastroLead,
    QualificacaoLead,
    ValidarLinkConclusaoB2C,
)
from ..dto.output import (
    HttpStatus,
    LeadPersistencia,
    LeadPreCadastroB2COutput,
    LeadPreCadastroOutput,
    Metadados,
)
from ..dto.types import listar_categorias_contato_validas
from ..router import Router
from ..utils.payload import (
    montar_dto_persistencia,
    montar_dto_pre_cadastro_b2c,
    montar_dto_qualificacao_persistencia,
    montar_payload_expa,
    montar_payload_expa_complemento,
)

new_lead_ogx: Router = Router(
    name="cadatro_interesse_intercambio", url_prefix="/new-lead-ogx"
)
logger: logging.Logger = logging.getLogger(__name__)


def _erro_integracao(
    servico: str,
    status: int,
    resposta: Any,
    mensagem_padrao: str,
) -> BaseErrorResponse:
    """Padroniza falhas de serviços externos sem descartar a causa original."""
    detalhe: str = mensagem_padrao
    if isinstance(resposta, dict):
        detalhe = next(
            (
                str(resposta[chave])
                for chave in ("erro", "error", "mensagem", "message")
                if resposta.get(chave)
            ),
            mensagem_padrao,
        )
    elif resposta is not None:
        detalhe = str(resposta)

    return BaseErrorResponse(
        type="ExternalServiceError",
        message=f"{servico} rejeitou a solicitação (HTTP {status}).",
        error_details=[{"loc": servico, "msg": detalhe}],
        status_code=HttpStatus.BAD_GATEWAY,
    )


def _mensagem_conflito_b2c(resposta: Any) -> str:
    """Preserva o motivo específico de duplicidade retornado pelo Apps Script."""
    if isinstance(resposta, dict):
        for chave in ("error", "message", "erro", "mensagem"):
            valor: Any = resposta.get(chave)
            if isinstance(valor, str) and valor.strip():
                return valor.strip()

        detalhes: Any = resposta.get("error_details")
        if isinstance(detalhes, list):
            for detalhe in detalhes:
                if isinstance(detalhe, dict):
                    mensagem: Any = detalhe.get("msg")
                    if isinstance(mensagem, str) and mensagem.strip():
                        return mensagem.strip()

    return "Já existe um cadastro para este usuário."


def _status_falha_b2c(resposta: Any) -> int | None:
    """Converte falhas internas do Apps Script, que podem chegar como HTTP 200."""
    if not isinstance(resposta, dict):
        return HttpStatus.BAD_GATEWAY
    if resposta.get("success") is not False:
        return None

    status: Any = resposta.get("status")
    if (
        isinstance(status, int)
        and not isinstance(status, bool)
        and 400 <= status < 600
    ):
        return status
    return HttpStatus.INTERNAL_SERVER_ERROR


def _resposta_falha_b2c(resposta: Any) -> dict[str, Any]:
    """Evita expor respostas HTML ou texto arbitrário do Apps Script."""
    if isinstance(resposta, dict):
        return resposta
    return {"error": "O Apps Script retornou uma resposta que não é JSON."}


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
        log_resposta_externa(logger, f"metadados B2C ({status_name})", status, payload)
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
    metadata_data: dict[str, Any] = {
        **metadata["data"],
        "categorias_contato": listar_categorias_contato_validas(),
    }
    metadata["data"] = metadata_data
    return metadata, status


@new_lead_ogx.post(
    "/cadastro-b2c/validar",
    summary="Validar link de conclusão B2C",
    tags=[Tag(name="New Lead OGX")],
    responses={
        200: {"description": "O cadastro pode ser concluído."},
        404: BaseErrorResponse,
        409: BaseErrorResponse,
        422: ValidationErrorResponse,
        502: BaseErrorResponse,
    },
)
def validar_link_conclusao(
    body: ValidarLinkConclusaoB2C,
) -> tuple[dict[str, Any] | BaseErrorResponse, int]:
    """Confere no Apps Script se o ID interno ainda está apto à conclusão."""
    status_b2c: int
    resposta_b2c: Any
    status_b2c, resposta_b2c = async_to_sync(validar_link_conclusao_b2c)(body.id)

    if not 200 <= status_b2c < 300:
        log_resposta_externa(
            logger, "validação de link B2C", status_b2c, resposta_b2c
        )
        return (
            _erro_integracao(
                "B2C",
                status_b2c,
                resposta_b2c,
                "Não foi possível validar o link de conclusão.",
            ),
            HttpStatus.BAD_GATEWAY,
        )

    status_falha: int | None = _status_falha_b2c(resposta_b2c)
    if status_falha == HttpStatus.NOT_FOUND:
        mensagem = "Cadastro não encontrado. Este link é inválido."
        return (
            BaseErrorResponse(
                type="InvalidCompletionLinkError",
                message=mensagem,
                error_details=[{"loc": "id", "msg": mensagem}],
                status_code=HttpStatus.NOT_FOUND,
            ),
            HttpStatus.NOT_FOUND,
        )

    if status_falha == HttpStatus.CONFLICT:
        mensagem = "Você já concluiu seu cadastro. Este link não é mais válido."
        return (
            BaseErrorResponse(
                type="ConflictError",
                message=mensagem,
                error_details=[{"loc": "id", "msg": mensagem}],
                status_code=HttpStatus.CONFLICT,
            ),
            HttpStatus.CONFLICT,
        )

    if status_falha is not None or not isinstance(resposta_b2c, dict) or (
        resposta_b2c.get("success") is not True
    ):
        resposta_falha = _resposta_falha_b2c(resposta_b2c)
        log_resposta_externa(
            logger,
            "validação de link B2C",
            status_falha or HttpStatus.BAD_GATEWAY,
            resposta_falha,
        )
        return (
            _erro_integracao(
                "B2C",
                status_falha or HttpStatus.BAD_GATEWAY,
                resposta_falha,
                "O Apps Script não confirmou a validade do link.",
            ),
            HttpStatus.BAD_GATEWAY,
        )

    return {"valid": True}, HttpStatus.OK


cadastro_b2c_view: APIView = APIView(
    view_tags=[Tag(name="New Lead OGX")],
    url_prefix=new_lead_ogx.url_prefix,
)


@cadastro_b2c_view.route("/cadastro-b2c")
class CadastroB2CView:
    """Agrupa a criação e a conclusão do cadastro B2C."""

    @cadastro_b2c_view.doc(
        summary="Criar pré-cadastro B2C",
        description=(
            "Recebe os campos do formulário B2C, sem senha ou criação de cadastro "
            "no EXPA, e envia o payload de pré-cadastro diretamente ao Apps Script B2C."
        ),
        responses={
            201: LeadPreCadastroB2COutput,
            409: BaseErrorResponse,
            502: BaseErrorResponse,
            422: ValidationErrorResponse,
            500: BaseErrorResponse,
            "default": {
                "description": "Erro HTTP exibido na página genérica de erro.",
                "content": {"text/html": {"schema": {"type": "string"}}},
            },
        },
    )
    def post(
        self: Self, body: CriarPreCadastroB2C
    ) -> tuple[LeadPreCadastroB2COutput | BaseErrorResponse, int]:
        """Envia ao B2C os campos recebidos do formulário de atração."""
        try:
            cadastro_b2c = montar_dto_pre_cadastro_b2c(body)
            payload_b2c: dict[str, Any] = cadastro_b2c.model_dump(mode="json")
        except (TypeError, ValueError) as error:
            logger.exception("Não foi possível montar o payload do pré-cadastro B2C")
            return (
                BaseErrorResponse(
                    type="PayloadPreparationError",
                    message="Não foi possível preparar o pré-cadastro B2C.",
                    error_details=[{"loc": "body", "msg": str(error)}],
                    status_code=HttpStatus.INTERNAL_SERVER_ERROR,
                ),
                HttpStatus.INTERNAL_SERVER_ERROR,
            )

        status_b2c: int
        resposta_b2c: Any
        status_b2c, resposta_b2c = async_to_sync(enviar_lead_b2c)(payload_b2c)

        status_informado: Any = (
            resposta_b2c.get("status") if isinstance(resposta_b2c, dict) else None
        )
        if status_b2c == HttpStatus.CONFLICT or status_informado == HttpStatus.CONFLICT:
            mensagem: str = _mensagem_conflito_b2c(resposta_b2c)
            logger.info("Cadastro B2C rejeitado por duplicidade")
            return (
                BaseErrorResponse(
                    type="ConflictError",
                    message=mensagem,
                    error_details=[{"loc": "B2C", "msg": mensagem}],
                    status_code=HttpStatus.CONFLICT,
                ),
                HttpStatus.CONFLICT,
            )

        if not 200 <= status_b2c < 300:
            log_resposta_externa(logger, "B2C pré-cadastro", status_b2c, resposta_b2c)
            return (
                _erro_integracao(
                    "B2C",
                    status_b2c,
                    resposta_b2c,
                    "Falha ao enviar pré-cadastro ao B2C.",
                ),
                HttpStatus.BAD_GATEWAY,
            )

        status_falha: int | None = _status_falha_b2c(resposta_b2c)
        if status_falha is not None:
            resposta_falha: dict[str, Any] = _resposta_falha_b2c(resposta_b2c)
            log_resposta_externa(
                logger, "B2C pré-cadastro", status_falha, resposta_falha
            )
            return (
                _erro_integracao(
                    "B2C",
                    status_falha,
                    resposta_falha,
                    "O Apps Script não confirmou a persistência do pré-cadastro.",
                ),
                HttpStatus.BAD_GATEWAY,
            )

        return LeadPreCadastroB2COutput.model_validate(payload_b2c), HttpStatus.CREATED

    @cadastro_b2c_view.doc(
        summary="Completar cadastro B2C",
        description=(
            "Valida o link, cria o cadastro do lead no EXPA e encaminha os dados "
            "complementares ao Apps Script B2C, incluindo o person_id retornado."
        ),
        responses={
            200: {"description": "Cadastro B2C concluído."},
            409: BaseErrorResponse,
            502: BaseErrorResponse,
            422: ValidationErrorResponse,
            "default": {
                "description": "Erro HTTP exibido na página genérica de erro.",
                "content": {"text/html": {"schema": {"type": "string"}}},
            },
        },
    )
    def put(
        self: Self, body: CompletarCadastroB2C
    ) -> tuple[dict[str, Any] | BaseErrorResponse, int]:
        """Cria o lead no EXPA e atualiza o pré-cadastro B2C."""
        resposta_validacao, status_validacao = validar_link_conclusao(
            ValidarLinkConclusaoB2C(id=body.id)
        )
        if status_validacao != HttpStatus.OK:
            return resposta_validacao, status_validacao

        payload_expa: Any = montar_payload_expa_complemento(body)
        status_b2c: int
        resposta_b2c: Any
        status_expa: int
        resposta_expa: Any
        status_expa, resposta_expa = async_to_sync(enviar_payload_expa)(
            payload_expa
        )

        if not 200 <= status_expa < 300:
            log_resposta_externa(
                logger, "EXPA conclusão de cadastro", status_expa, resposta_expa
            )
            return (
                _erro_integracao(
                    "EXPA",
                    status_expa,
                    resposta_expa,
                    "Falha ao criar cadastro no EXPA.",
                ),
                HttpStatus.BAD_GATEWAY,
            )

        if (
            not isinstance(resposta_expa, dict)
            or resposta_expa.get("sucesso") is not True
        ):
            status_expa_informado: Any = (
                resposta_expa.get("status_code")
                if isinstance(resposta_expa, dict)
                else None
            )
            if (
                not isinstance(status_expa_informado, int)
                or isinstance(status_expa_informado, bool)
                or not 400 <= status_expa_informado < 600
            ):
                status_expa_informado = HttpStatus.BAD_GATEWAY
            log_resposta_externa(
                logger,
                "EXPA confirmação de conclusão",
                status_expa_informado,
                resposta_expa,
            )
            return (
                _erro_integracao(
                    "EXPA",
                    status_expa_informado,
                    resposta_expa,
                    "O EXPA não confirmou a criação do cadastro.",
                ),
                HttpStatus.BAD_GATEWAY,
            )

        person_id: Any = resposta_expa.get("person_id")
        if (
            not isinstance(person_id, (str, int))
            or isinstance(person_id, bool)
            or not str(person_id).isdigit()
            or int(person_id) <= 0
        ):
            log_resposta_externa(
                logger,
                "EXPA person_id ausente ou inválido na conclusão",
                HttpStatus.BAD_GATEWAY,
                resposta_expa,
            )
            return (
                _erro_integracao(
                    "EXPA",
                    HttpStatus.BAD_GATEWAY,
                    resposta_expa,
                    "Resposta do EXPA sem person_id válido.",
                ),
                HttpStatus.BAD_GATEWAY,
            )

        payload_b2c: dict[str, Any] = body.model_dump(
            mode="json",
            exclude={"idProgramaExpa", "senha"},
            exclude_none=True,
        )
        payload_b2c["idExpa"] = int(person_id)
        payload_b2c["status"] = "completar-cadastro"
        status_b2c, resposta_b2c = async_to_sync(enviar_lead_b2c)(payload_b2c)

        status_informado: Any = (
            resposta_b2c.get("status") if isinstance(resposta_b2c, dict) else None
        )
        if status_b2c == HttpStatus.CONFLICT or status_informado == HttpStatus.CONFLICT:
            mensagem: str = _mensagem_conflito_b2c(resposta_b2c)
            logger.info("Conclusão de cadastro B2C rejeitada por conflito")
            return (
                BaseErrorResponse(
                    type="ConflictError",
                    message=mensagem,
                    error_details=[{"loc": "B2C", "msg": mensagem}],
                    status_code=HttpStatus.CONFLICT,
                ),
                HttpStatus.CONFLICT,
            )

        if not 200 <= status_b2c < 300:
            log_resposta_externa(
                logger, "B2C conclusão de cadastro", status_b2c, resposta_b2c
            )
            return (
                _erro_integracao(
                    "B2C",
                    status_b2c,
                    resposta_b2c,
                    "Falha ao concluir o cadastro B2C.",
                ),
                HttpStatus.BAD_GATEWAY,
            )

        status_falha: int | None = _status_falha_b2c(resposta_b2c)
        if status_falha is not None:
            resposta_falha: dict[str, Any] = _resposta_falha_b2c(resposta_b2c)
            log_resposta_externa(
                logger, "B2C conclusão de cadastro", status_falha, resposta_falha
            )
            return (
                _erro_integracao(
                    "B2C",
                    status_falha,
                    resposta_falha,
                    "O Apps Script não confirmou a conclusão do cadastro.",
                ),
                HttpStatus.BAD_GATEWAY,
            )

        logger.info("Cadastro B2C concluído | lead %s", body.id)
        return {"id": body.id, "status": "cadastro completo"}, HttpStatus.OK


# ==============================================================================
# DOCUMENTAÇÃO DAS OPERAÇÕES DE CADASTRO
# ==============================================================================
CADASTRO_POST_DESCRIPTION: str = """\
Recebe os dados da primeira etapa, cria o lead no EXPA e retorna o DTO de
persistência com o `id` (`person_id`) retornado pelo EXPA e status
`pré-cadastro`. Envia o payload ao B2C com esse status fixo. A senha não é
devolvida."""

CADASTRO_PUT_DESCRIPTION: str = """\
Recebe os dados complementares da segunda etapa e atualiza o lead criado no
pré-cadastro. Envia os dados ao B2C com o status fixo `qualificação`."""

CADASTRO_POST_RESPONSES: dict[int | str, Any] = {
    201: LeadPersistencia,
    502: BaseErrorResponse,
    422: ValidationErrorResponse,
    "default": {
        "description": "Erro HTTP exibido na página genérica de erro.",
        "content": {"text/html": {"schema": {"type": "string"}}},
    },
}

CADASTRO_PUT_RESPONSES: dict[int | str, Any] = {
    200: {"description": "Dados de qualificação enviados ao B2C."},
    502: BaseErrorResponse,
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
    ) -> tuple[LeadPersistencia | BaseErrorResponse, int]:
        """Cria o lead no EXPA e retorna os dados para persistência."""
        payload: Any = montar_payload_expa(body)
        status: int
        resposta: Any
        status, resposta = async_to_sync(enviar_payload_expa)(payload)

        if not 200 <= status < 300 and status != 401:
            log_resposta_externa(logger, "EXPA criação de lead", status, resposta)
            return (
                _erro_integracao(
                    "EXPA",
                    status,
                    resposta,
                    "Falha ao criar lead no EXPA.",
                ),
                HttpStatus.BAD_GATEWAY,
            )

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
            if status_expa != 401:
                log_resposta_externa(
                    logger,
                    "EXPA confirmação de criação",
                    status_expa,
                    resposta,
                )
                return (
                    _erro_integracao(
                        "EXPA",
                        int(status_expa),
                        resposta,
                        "O EXPA não confirmou a criação.",
                    ),
                    HttpStatus.BAD_GATEWAY,
                )

        person_id: Any = resposta.get("person_id")
        if (
            not isinstance(person_id, (str, int))
            or isinstance(person_id, bool)
            or not str(person_id).isdigit()
            or int(person_id) <= 0
        ):
            log_resposta_externa(
                logger,
                "EXPA person_id ausente ou inválido",
                int(HttpStatus.BAD_GATEWAY),
                resposta,
            )
            return (
                _erro_integracao(
                    "EXPA",
                    int(HttpStatus.BAD_GATEWAY),
                    resposta,
                    "Resposta do EXPA sem person_id válido.",
                ),
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

        payload_b2c: dict[str, Any] = lead_persistencia.model_dump(mode="json")
        payload_b2c["status"] = "pré-cadastro"
        status_b2c: int
        resposta_b2c: Any
        status_b2c, resposta_b2c = async_to_sync(enviar_lead_b2c)(payload_b2c)
        if not 200 <= status_b2c < 300:
            log_resposta_externa(
                logger, "B2C pré-cadastro EXPA", status_b2c, resposta_b2c
            )
            return (
                _erro_integracao(
                    "B2C",
                    status_b2c,
                    resposta_b2c,
                    "Falha ao enviar lead ao B2C.",
                ),
                HttpStatus.BAD_GATEWAY,
            )

        return lead_persistencia, HttpStatus.CREATED

    @cadastro_lead_view.doc(
        summary="Atualizar cadastro do lead",
        description=CADASTRO_PUT_DESCRIPTION,
        responses=CADASTRO_PUT_RESPONSES,
    )
    def put(self: Self, body: QualificacaoLead) -> tuple[Any, int]:
        """Envia ao B2C os dados complementares da segunda etapa."""
        qualificacao_persistencia = montar_dto_qualificacao_persistencia(body)
        payload_b2c: dict[str, Any] = qualificacao_persistencia.model_dump(
            mode="json",
            by_alias=True,
            exclude_unset=True,
        )
        status_b2c: int
        resposta_b2c: Any
        status_b2c, resposta_b2c = async_to_sync(enviar_lead_b2c)(payload_b2c)

        if not 200 <= status_b2c < 300:
            log_resposta_externa(logger, "B2C qualificação", status_b2c, resposta_b2c)
            return (
                _erro_integracao(
                    "B2C",
                    status_b2c,
                    resposta_b2c,
                    "Falha ao enviar dados de qualificação ao B2C.",
                ),
                HttpStatus.BAD_GATEWAY,
            )

        logger.info("Dados de qualificação enviados ao B2C | lead %s", body.id)
        return payload_b2c, status_b2c


__all__ = ["cadastro_b2c_view", "cadastro_lead_view", "new_lead_ogx"]
