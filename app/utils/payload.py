"""Montagem de payloads de cadastro para persistência."""

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel

from ..dto.common import CategoriaContato
from ..dto.input import CriarPreCadastroLead


def _id_tipo_contato(contato: Any, nome_campo: str, indice: int) -> int:
    """Obtém o ID de persistência do tipo de um contato validado ou em dict."""
    if isinstance(contato, BaseModel):
        tipo: Any = getattr(contato, "tipo", None)
    elif isinstance(contato, Mapping):
        tipo = contato.get("tipo")
    else:
        tipo = None

    if isinstance(tipo, CategoriaContato):
        categoria: CategoriaContato = tipo
    else:
        try:
            categoria = CategoriaContato(tipo)
        except (TypeError, ValueError) as erro:
            raise ValueError(
                f"Tipo de contato inválido em {nome_campo}[{indice}].tipo."
            ) from erro

    return categoria.id_persistencia


def montar_payload_persistencia(modelo: BaseModel) -> dict[str, Any]:
    """Gera o payload completo, trocando o texto do tipo de contato pelo ID.

    Os demais campos e a estrutura recebida são preservados. Campos opcionais
    omitidos no request continuam omitidos; valores explicitamente nulos são
    mantidos.
    """
    payload: dict[str, Any] = modelo.model_dump(
        mode="json",
        by_alias=True,
        exclude_unset=True,
    )

    for nome_campo in ("telefone", "email"):
        contatos: Any = getattr(modelo, nome_campo, None)
        contatos_payload: Any = payload.get(nome_campo)
        if not isinstance(contatos, list) or not isinstance(contatos_payload, list):
            continue

        for indice, contato in enumerate(contatos):
            if indice < len(contatos_payload) and isinstance(contatos_payload[indice], dict):
                contatos_payload[indice]["tipo"] = _id_tipo_contato(
                    contato, nome_campo, indice
                )

    return payload


def _normalizar_nome_escritorio(nome: str) -> str:
    """Remove os prefixos usados nos nomes de escritórios da AIESEC."""
    return (
        nome.replace("AIESEC em São Paulo Unidade", "")
        .replace("AIESEC em", "")
        .replace("AIESEC no", "")
        .strip()
    )


def _resolver_nome_cl_expa(dados: CriarPreCadastroLead) -> str:
    """Resolve o comitê EXPA pela divisão de mercado histórica."""
    from app.cache import cache

    divisao: dict[str, Any] | None = None
    if dados.universidade:
        universidades: Any = cache.store.get(
            "metadados_universidades", {}
        ).get("data", {}).get("dados", [])
        divisao = next(
            (
                universidade
                for universidade in universidades
                if isinstance(universidade, dict)
                and universidade.get("nome") == dados.universidade.nome
            ),
            None,
        )
    elif dados.comite:
        escritorios: Any = cache.store.get(
            "metadados_escritorios", {}
        ).get("data", {}).get("dados", [])
        nome_comite: str = _normalizar_nome_escritorio(dados.comite.nome).title()
        divisao = next(
            (
                escritorio
                for escritorio in escritorios
                if isinstance(escritorio, dict)
                and isinstance(escritorio.get("nome"), str)
                and escritorio["nome"].title() == nome_comite
            ),
            None,
        )

    if divisao is None:
        raise ValueError(
            "Não foi possível resolver o comitê EXPA: divisão de mercado "
            "indisponível ou sem correspondência."
        )

    chave_produto: str = "gv" if dados.produto.id_expa == 7 else "gt"
    nome_cl: Any = divisao.get(chave_produto)
    if nome_cl == "MC BAZI":
        return "AIESEC no Brasil"
    if not isinstance(nome_cl, str) or not nome_cl.strip():
        raise ValueError(
            f"A divisão de mercado não contém o comitê '{chave_produto}' para EXPA."
        )
    return nome_cl


def montar_payload_expa(dados: CriarPreCadastroLead) -> dict[str, Any]:
    """Monta o payload plano do EXPA com a resolução histórica de comitê."""
    nome_cl_formatado: str = _normalizar_nome_escritorio(
        _resolver_nome_cl_expa(dados)
    )
    return {
        "nome": str(dados.nome).title(),
        "sobrenome": str(dados.sobrenome).title(),
        "senha": str(dados.senha),
        "dataNascimento": str(dados.dataNascimento),
        "programa": int(dados.produto.id_expa),
        "nomeCL": nome_cl_formatado,
        "telefone": str(dados.telefone[0].numero) if dados.telefone else "",
        "email": str(dados.email[0].email) if dados.email else "",
    }


def payload_expa(dados: CriarPreCadastroLead) -> dict[str, Any]:
    """Nome histórico do builder de cadastro EXPA."""
    return montar_payload_expa(dados)


__all__ = [
    "montar_payload_persistencia",
    "montar_payload_expa",
    "payload_expa",
]
