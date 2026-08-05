"""Módulo de integração para criação e sincronização assíncrona de Leads.

Este módulo orquestra o fluxo de cadastro em duas etapas principais:
    1. Registro inicial na plataforma EXPA via Google Apps Script para geração do 'person_id'.
    2. Criação do card do Lead no Podio com o ID do EXPA vinculado e gestão de fallback
       automático de token de acesso expirado.
"""

# modulo de tipos
from typing import Any, Dict

# Importação da função utilitária para desempacotar respostas HTTP
from app.utils import resolve_response

# Importação da classe cliente HTTP customizada
from ..http_request import HttpClient

# Importação das funções utilitárias do Podio
from .podio import buscar_id_card, buscar_token

from app.dto import ErroGenerico,HttpStatus

# Cliente base pré-configurado para a API do Podio
http = HttpClient(base_url="https://api.podio.com", prefix="/item/app")


@validar
async def adicionar_lead(
        chave: str,
        payload: Dict[str, Any],
        payload_expa: Dict[str, Any],
        app_id: int,
        response_dto: Dict[str, Any],
) -> tuple[Any, HttpStatus] | dict[str, Any]:
    """Cria a conta do lead no EXPA e insere o card correspondente no Podio.

    O processo executa os seguintes passos:
        1. Envia o `payload_expa` ao AppScript do EXPA para obter o identificador único (`person_id`).
        2. Atualiza o `payload` do Podio inserindo o `person_id` no campo referente ao EP ID (`di-ep-id-2`).
        3. Realiza a requisição POST para criação do item no Podio no aplicativo informado por `app_id`.
        4. Trata erros HTTP da família 4xx (exceto 405) como potencial token expirado, forçando a atualização
           do token no cache centralizado (`resync=True`) e reexecutando a requisição.
        5. Atribui o ID gerado pelo Podio à chave `'id'` do dicionário de resposta.

    Args:
        chave (str): Chave identificadora da configuração de serviço/token no cache (ex: 'ogx-token-podio').
        payload (Dict[str, Any]): Estrutura de campos e valores no formato esperado pela API do Podio.
        payload_expa (Dict[str, Any]): Dicionário com dados do lead formatados para o endpoint do EXPA.
        app_id (int): Identificador numérico do aplicativo no Podio alvo da criação.
        response_dto (Dict[str, Any]): Dicionário base derivado do DTO de entrada para composição do retorno.

    Returns:
        Dict[str, Any]: Dicionário consolidado com os dados do lead incluindo o 'id' gerado pelo Podio.

    Raises:
        ValueError: Disparado se a requisição ao EXPA falhar, se o Podio retornar status diferente de 2xx/3xx
            após a tentativa de fallback, ou se ocorrer erro genérico no desempacotamento das respostas HTTP.
    """
    # Lazy imports para evitar dependências circulares durante a inicialização dos módulos
    from app.cache import cache # cache da memoria
    from app.middlewares.registrando_token_rota import CONFIG_MAP, _fetch_token # funções de cache
    # Importação das variáveis de ambiente e configurações do EXPA
    from app.core import APPSCRIPT_EXPA, TOKEN_EXPA

    # Cliente base pré-configurado para a API do AppScript EXPA
    http_expa = HttpClient(base_url=APPSCRIPT_EXPA)

    # === STEP 1: CADASTRO E OBTENÇÃO DE ID NO EXPA ===
    # Injeta a credencial global do EXPA necessária para autorização na API
    payload_expa["tokenExpa"] = TOKEN_EXPA

    try:
        # Envia os dados do lead para a API intermediária do EXPA
        res_expa = http_expa.post(payload=payload_expa)
        status_expa, data_expa = await resolve_response(res_expa)
        # Valida se a resposta do EXPA permaneceu no intervalo de sucesso (200-399)
        if not data_expa["sucesso"]:
            sucess = data_expa.pop("sucesso")
            return ErroGenerico[dict](
                sucesso=sucess,
                dados=data_expa
            ).model_dump(),HttpStatus.BAD_REQUEST

        # Insere o EP ID do EXPA dentro da estrutura de campos do Podio
        payload["fields"]["di-ep-id-2"] = data_expa.get("person_id")

    except Exception as err:
        raise ValueError(f"Falha ao cadastrar lead no EXPA: {err}")

    # === STEP 2: CADASTRO NO PODIO COM REFRESH AUTOMÁTICO DE TOKEN ===
    # Prepara os cabeçalhos padrão de autorização e tipo de conteúdo
    headers = {
        "Authorization": f"Bearer {buscar_token(chave)}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Primeira tentativa de criação do item na API do Podio
    res_podio = http.post(path=f"/{app_id}", payload=payload, headers=headers)
    status, data = await resolve_response(res_podio)

    # Trata erros da faixa 4xx (como 401 Unauthorized), forçando resync do token no cache
    if 400 <= status <= 499 and status != 405:
        service = "new-lead-ogx"
        config = CONFIG_MAP.get(service)

        if config:
            # Força a atualização do token ignorando o valor antigo em cache
            await cache.get_or_set(
                key=chave,
                fetch=_fetch_token,
                baixando=f"Chave de Acesso ao Podio ({service})",
                resync=True,
            )

            # Reconfigura os cabeçalhos com o novo token atualizado
            headers["Authorization"] = f"Bearer {buscar_token(chave)}"

            # Segunda tentativa de criação do item no Podio
            res_podio = http.post(path=f"/{app_id}", payload=payload, headers=headers)
            status, data = await resolve_response(res_podio)

    # Garante que a requisição no Podio foi concluída com sucesso
    if not 200 <= status <= 399:
        raise ValueError(f"Falha ao adicionar lead no Podio ({status}): {data}")
    print(payload)
    # === STEP 3: PREPARAÇÃO E RETORNO DA RESPOSTA FINAL ===
    # Atribui o ID extraído do Podio à chave 'id' exigida pelo DTO de saída (LeadPreCadastroOutput)
    response_dto["item_id"] = buscar_id_card(data)

    return response_dto,HttpStatus.CREATED


__all__ = ["adicionar_lead"]