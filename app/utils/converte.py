# Módulo nativo do Python para manipulação de tipos internos e dinâmicos (ex: types.UnionType)
import types

# Módulo nativo de anotações e reflexão de tipos (usado para desempacotar Unions e Genéricos)
from typing import Any, Dict, List, Tuple, Union, get_args, get_origin

# Componentes do Flask para manipulação e formatação da resposta HTTP em JSON
from flask import Response, jsonify

# Componentes do Pydantic v2 para validação de schemas e captura de exceções
from pydantic import BaseModel, ValidationError


def _extrair_candidatos_union(annotation: Any) -> List[Any]:
    """Extrai recursivamente todos os tipos contidos em anotações Union ou Optional.

    Trata tanto a sintaxe `typing.Union` / `typing.Optional` quanto o operador
    de união de tipos `|` (Python 3.10+ / `types.UnionType`).

    Args:
        annotation (Any): A anotação de tipo a ser inspecionada (ex: `Union[A, B]`,
            `Optional[dict]`, ou `ConflitosLeadOutput`).

    Returns:
        List[Any]: Uma lista plana contendo todas as classes/tipos individuais
        presentes na união. Caso a anotação não seja uma Union, retorna uma lista
        unitária com a própria anotação.

    Example:
        >>> _extrair_candidatos_union(Union[ConflitosLeadOutput, dict, None])
        [ConflitosLeadOutput, dict, NoneType]
    """
    origin = get_origin(annotation)
    eh_union = origin is Union or (
            hasattr(types, "UnionType") and origin is types.UnionType
    )

    # Se a anotação for uma Union, desempacota recursivamente seus argumentos de tipo
    if eh_union:
        candidatos = []
        for arg in get_args(annotation):
            candidatos.extend(_extrair_candidatos_union(arg))
        return candidatos

    return [annotation]


def _testar_union_um_a_um(valor: Any, tipo_annotation: Any) -> Any:
    """Testa e sanitiza um valor contra os tipos declarados em uma Union de forma sequencial.

    Diferente do comportamento nativo do Pydantic (que aceita o primeiro match
    mesmo descartando chaves não mapeadas em schemas com `extra="ignore"`), esta
    função impõe validação estrita: se a conversão para um DTO derivado de `BaseModel`
    resultar em um dicionário vazio (`{}`), assume-se incompatibilidade de schema
    e faz-se fallback para os demais candidatos genéricos (como `dict`).

    Args:
        valor (Any): O payload retornado na chave 'data' que precisa ser validado.
        tipo_annotation (Any): A anotação de tipo do campo 'data' extraída do modelo.

    Returns:
        Any: O payload devidamente validado e sanitizado (como `dict` filtrado de DTO
        ou dicionário bruto caso o fallback para `dict` seja acionado).
    """
    if valor is None:
        return None

    # Se o valor já for uma instância de BaseModel, converte para dict sanitizado
    if isinstance(valor, BaseModel):
        valor = valor.model_dump(exclude_none=True)

    # Resolve e achata a hierarquia da Union em uma lista de candidatos
    candidatos = _extrair_candidatos_union(tipo_annotation)

    modelos_pydantic: List[type] = []
    outros_tipos: List[type] = []

    # Separa candidatos DTO (BaseModel) de tipos primitivos/genéricos (dict, str, etc.)
    for c in candidatos:
        if c is type(None):
            continue
        real_cls = get_origin(c) or c
        if isinstance(real_cls, type) and issubclass(real_cls, BaseModel):
            modelos_pydantic.append(c)
        else:
            outros_tipos.append(c)

    # 1. ETAPA 1: Tenta validação estrita contra os DTOs Pydantic registrados na Union
    if isinstance(valor, dict) and valor:
        for model_cls in modelos_pydantic:
            # 💡 Usa getattr para acessar model_validate sem disparar o alerta do PyCharm
            validador = getattr(model_cls, "model_validate", None)
            if callable(validador):
                try:
                    instancia = model_cls.model_validate(valor)
                    dados = instancia.model_dump(exclude_none=True)

                    # 💡 REGRA ANTI-PERDA DE DADOS:
                    # Se o DTO aproveitou ao menos uma chave do dicionário original,
                    # aceita a conversão. Se 'dados' ficou vazio ({}), significa que
                    # o Pydantic descartou todas as chaves via 'extra="ignore"', logo o
                    # payload não pertencia a este DTO.
                    if dados:
                        return dados
                except ValidationError:
                    # Falha de campo obrigatório ou tipo incorreto; passa para o próximo DTO
                    continue

    # 2. ETAPA 2: Fallback para tipos genéricos não estruturados (ex: dict)
    for tipo in outros_tipos:
        if tipo is dict and isinstance(valor, dict):
            return valor

    return valor


def converter_resposta_dinamica(
        response: Union[Tuple[Any, int], Any], responses: Dict[Union[int, str], Any]
) -> Union[Tuple[Response, int], Any]:
    """Callback de interceptação e sanitização de respostas HTTP para o Flask-OpenAPI3.

    Inspeciona dinamicamente o modelo Pydantic registrado para o status code HTTP
    retornado pela rota, realizando:
      1. Empacotamento automático em envelope (`{"sucesso": bool, "data": ...}`) quando
         a rota retorna o payload diretamente.
      2. Resolução sequencial de tipos `Union` no campo `data` (ex: `Union[DTO, dict]`),
         evitando perda de dados por descarte silencioso de chaves.
      3. Serialização final para JSON formatado via `jsonify` do Flask.

    Args:
        response (Union[Tuple[Any, int], Any]): O retorno nativo da função da rota Flask.
            Pode ser um payload direto (dict, BaseModel) ou uma tupla `(payload, status_code)`.
        responses (Dict[Union[int, str], Any]): Dicionário de schemas configurados no
            decorator da rota pelo Flask-OpenAPI3, mapeando status HTTP (int ou str)
            para modelos Pydantic ou genéricos parametrizados.

    Returns:
        Union[Tuple[Response, int], Any]: Tupla `(Response JSON do Flask, status_code)` contendo
        o payload sanitizado e formatado, ou a resposta original intacta caso nenhum
        modelo Pydantic esteja registrado para o status HTTP em questão.
    """
    # 1. Desempacota a resposta HTTP e extrai o payload e o status_code
    if isinstance(response, tuple):
        payload, status_code = response[0], response[1]
    else:
        payload, status_code = response, 200

    # 2. Se o payload da rota for uma instância direta de BaseModel, converte para dict
    if isinstance(payload, BaseModel):
        payload = payload.model_dump(exclude_none=True)

    # 3. Trata status_code do tipo Enum (ex: HTTPStatus.OK -> 200)
    code_key = getattr(status_code, "value", status_code)

    # 4. Busca o schema Pydantic registrado no Flask-OpenAPI3 para esse status code
    model_cls = responses.get(code_key) or responses.get(str(code_key))

    # Se não houver modelo registrado na rota para este status, retorna a resposta original
    if model_cls is None:
        return response

    # 5. Resolve a classe concreta caso venha parametrizada (ex: RetornoGenerico[T])
    actual_cls = get_origin(model_cls) or model_cls

    # 6. Processa se a classe principal for um BaseModel e o payload for dicionário
    if (
            isinstance(actual_cls, type)
            and issubclass(actual_cls, BaseModel)
            and isinstance(payload, dict)
    ):
        campos_do_modelo = getattr(model_cls, "model_fields", {})
        eh_envelope = "sucesso" in campos_do_modelo and "data" in campos_do_modelo

        # 7. EMPACOTAMENTO AUTOMÁTICO:
        # Se o modelo for um envelope e a rota retornou o payload direto (sem a chave 'data')
        if eh_envelope and "data" not in payload:
            sucesso_val = payload.pop("sucesso", 200 <= status_code <= 399)
            payload = {
                "sucesso": sucesso_val,
                "data": payload if payload else None,
            }

        # 8. PROCESSAMENTO DA UNION EM ENVELOPES:
        if eh_envelope and "data" in campos_do_modelo:
            annotation_data = campos_do_modelo["data"].annotation

            # Sanitiza o conteúdo da chave 'data' testando candidato por candidato
            payload["data"] = _testar_union_um_a_um(
                payload.get("data"), annotation_data
            )

            # 💡 RETORNO DIRETO:
            # Como payload['data'] já foi rigorosamente validado e sanitizado contra a Union,
            # retornamos o JSON diretamente para evitar que uma re-validação pelo model_cls
            # acione o comportamento padrão do Pydantic (extra="ignore") e descarte dados.
            return jsonify(payload), status_code

        # 9. Para schemas que não utilizam o padrão de envelope, faz a validação padrão
        instancia_validada = actual_cls.model_validate(payload)
        return jsonify(instancia_validada.model_dump(exclude_none=True)), status_code

    return response


__all__ = ["converter_resposta_dinamica"]