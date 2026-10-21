"""Montagem de payloads de cadastro para persistência."""

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel

from ..cache.cache import capitalizar_nome
from ..dto.common import CategoriaContato, PayloadExpa
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
    nome = nome.strip()
    for prefixo in (
        "AIESEC em São Paulo Unidade",
        "AIESEC em",
        "AIESEC no",
    ):
        if nome.casefold().startswith(prefixo.casefold()):
            return nome[len(prefixo):].strip()
    return nome


def _chave_nome_cache(nome: str) -> str:
    """Normaliza capitalização e espaços para comparar nomes do cache."""
    return capitalizar_nome(nome).casefold()


def _dados_divisao_cache(chave_cache: str) -> list[Any]:
    """Obtém os registros da divisão de mercado armazenados na chave informada."""
    from app.cache import cache

    entrada: Any = cache.store.get(chave_cache)
    dados_cache: Any = entrada.get("data") if isinstance(entrada, Mapping) else None
    registros: Any = (
        dados_cache.get("dados") if isinstance(dados_cache, Mapping) else None
    )
    return registros if isinstance(registros, list) else []


def _resolver_nome_cl_expa(dados: CriarPreCadastroLead) -> str:
    """Resolve o comitê EXPA pela divisão de mercado histórica."""
    divisao: dict[str, Any] | None = None
    if dados.universidade:
        universidades: list[Any] = _dados_divisao_cache(
            "metadados_universidades"
        )
        divisao = next(
            (
                universidade
                for universidade in universidades
                if isinstance(universidade, dict)
                and isinstance(universidade.get("nome"), str)
                and _chave_nome_cache(universidade["nome"])
                == _chave_nome_cache(dados.universidade)
            ),
            None,
        )
    elif dados.comite:
        escritorios: list[Any] = _dados_divisao_cache(
            "metadados_escritorios"
        )
        nome_comite: str = _chave_nome_cache(
            _normalizar_nome_escritorio(dados.comite.nome)
        )
        divisao = next(
            (
                escritorio
                for escritorio in escritorios
                if isinstance(escritorio, dict)
                and isinstance(escritorio.get("nome"), str)
                and _chave_nome_cache(escritorio["nome"]) == nome_comite
            ),
            None,
        )

    if divisao is None:
        raise ValueError(
            "Não foi possível resolver o comitê EXPA: divisão de mercado "
            "indisponível ou sem correspondência."
        )

    chave_produto: str = "oGV" if dados.produto.id_expa == 7 else "oGT"
    nome_cl: Any = divisao.get(chave_produto)
    if nome_cl == "MC BAZI":
        return "AIESEC no Brasil"
    if not isinstance(nome_cl, str) or not nome_cl.strip():
        raise ValueError(
            f"A divisão de mercado não contém o comitê '{chave_produto}' para EXPA."
        )
    return nome_cl


def montar_payload_expa(dados: CriarPreCadastroLead) -> PayloadExpa:
    """Monta o payload plano que o webhook GAS espera para criar no EXPA."""
    from app.config import TOKEN_EXPA

    nome_cl_formatado: str = _normalizar_nome_escritorio(
        _resolver_nome_cl_expa(dados)
    )
    return PayloadExpa(
        nome=str(dados.nome).title(),
        sobrenome=str(dados.sobrenome).title(),
        senha=str(dados.senha),
        data_nascimento=dados.dataNascimento.date().isoformat(),
        programa=int(dados.produto.id_expa),
        nome_cl=nome_cl_formatado,
        telefone=str(dados.telefone[0].numero) if dados.telefone else "",
        email=str(dados.email[0].email) if dados.email else "",
        token_expa=TOKEN_EXPA,
    )


def payload_expa(dados: CriarPreCadastroLead) -> PayloadExpa:
    """Nome histórico do builder de cadastro EXPA."""
    return montar_payload_expa(dados)


__all__ = [
    "montar_payload_persistencia",
    "montar_payload_expa",
    "payload_expa",
]
