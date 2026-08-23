"""
Helpers de formatação específicos da camada de apresentação/integração.

Atualmente contém utilitários para empacotar e transformar dados de DTOs
no formato esperado pelas APIs REST do Podio (chaves dentro do nó 'fields')
e da plataforma EXPA, além de estruturas de payload para upload e anexo de arquivos.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from typing import Any, Dict

from ..utils import formatar_texto

# Módulos de DTOs para validação e estruturação dos dados
from ..dto import (
    CategoriaContato,
    CriarPreCadastroLead,
    DataNascimento,
    LeadPreCadastroInput,
    LeadPreCadastroOutput,
    QualificacaoLead,
)


# =================================================================
# 2. FORMATADORES DE INTEGRAÇÃO COM A API DO PODIO E EXPA
# =================================================================

def payload_pre_cadastro_podio(data: LeadPreCadastroInput) -> Dict[str, Any]:
    """Constrói o payload padrão esperado pela API REST do Podio para pré-cadastro."""
    from app.cache import cache

    id_aiesec_mais_proxima = None
    escritorio_alocado = None

    if data.universidade:
        universidade_encontrada = next(
            (
                uni
                for uni in cache.store.get("divisao-mercado-universidades", {}).get("data", [])
                if uni.get("nome") == data.universidade.nome
            ),
            None,
        )

        if universidade_encontrada:
            # Seleciona a chave correta (gv para produto 7, caso contrário gt)
            chave_busca = "gv" if data.produto.id_expa == 7 else "gt"
            valor_bruto = universidade_encontrada.get(chave_busca, "")

            # Regra de negócio: Mapear "MC BAZI" para "AIESEC no Brasil"
            escritorio_alocado = "AIESEC no Brasil" if valor_bruto == "MC BAZI" else valor_bruto

    elif data.comite:
        escritorio_encontrado = next(
            (
                uni
                for uni in cache.store.get("divisao-mercado-escritorios", {}).get("data", [])
                if uni.get("nome").title() == data.comite.nome.replace("AIESEC em São Paulo Unidade", "")
                                                      .replace("AIESEC em", "")
                                                      .replace("AIESEC no", "")
                                                      .strip().title()
            ),
            None,
        )

        if escritorio_encontrado:
            chave_busca = "gv" if data.produto.id_expa == 7 else "gt"
            valor_bruto = escritorio_encontrado.get(chave_busca, "")
            escritorio_alocado = "AIESEC no Brasil" if valor_bruto == "MC BAZI" else valor_bruto


    if escritorio_alocado:
        # Busca o ID do escritório correspondente
        id_escritorio_alocado = next(
            (
                u
                for uni in cache.store.get("metadados_card-ogx", {}).get("data", [{}])
                if uni.get("external_id") == "aiesec-mais-proxima"
                for u in uni.get("options", [])
                if u.get("text", "")
                   .replace("AIESEC em São Paulo Unidade", "")
                   .replace("AIESEC em", "")
                   .replace("AIESEC no", "")
                   .strip().title()
                   == escritorio_alocado.replace("AIESEC em São Paulo Unidade", "").replace("AIESEC no", "").replace("AIESEC em", "").strip().title()
            ),
            None,
                   )

        if id_escritorio_alocado:
            id_aiesec_mais_proxima = id_escritorio_alocado.get("id")

    # Caso não tenha encontrado, cai no fallback do comitê padrão
    id_final_aiesec = id_aiesec_mais_proxima

    payload: Dict[str, Any] = {
        "fields": {
            "title": str(data.nome).title(),
            "sobrenome-2": str(data.sobrenome).title(),
            "email": [{"type": str(e.tipo.value), "value": str(e.email)} for e in data.email],
            "telefone": [{"type": str(t.tipo.value), "value": str(t.numero)} for t in data.telefone],
            "data-de-nascimento-2": str(data.dataNascimento),
            "produto": int(data.produto.id_podio),
            "aiesec-mais-proxima": id_final_aiesec,
            "tag-origem-2": int(data.origem.id),
            "status-expa": 1,
            "eu-concordo-com-a-coleta-e-uso-dos-meus-dados-conforme-": int(data.autorizacao),
        },
        "tags": [],
    }

    if data.universidade:
        payload["fields"]["universidade"] = str(data.universidade.nome)
    if data.meio:
        payload["fields"]["tag-meio-2-2"] = int(data.meio.id)
    if data.tag:
        payload["tags"] = data.tag if isinstance(data.tag, list) else [str(data.tag)]

    return payload


def payload_expa(data: CriarPreCadastroLead) -> Dict[str, Any]:
    """Formata e constrói o payload para a API do EXPA buscando o CL pela universidade ou comitê."""
    from app.cache import cache

    if data.universidade:
        universidade_encontrada = next(
            (
                uni
                for uni in cache.store.get("divisao-mercado-universidades", {}).get("data", [])
                if uni.get("nome") == data.universidade.nome
            ),
            None,
        )

        if universidade_encontrada:
            # Seleciona a chave correta (usando a mesma lógica do Podio)
            chave_busca = "gv" if data.produto.id_expa == 7 else "gt"
            valor_bruto = universidade_encontrada.get(chave_busca, "")

            # Regra de negócio: Se for "MC BAZI", mapear para "AIESEC no Brasil"
            if valor_bruto == "MC BAZI":
                nome_cl_formatado = "AIESEC no Brasil"
            elif valor_bruto:
                nome_cl_formatado = valor_bruto

    elif data.comite:
        escritorio_encontrado = next(
            (
                uni
                for uni in cache.store.get("divisao-mercado-escritorios", {}).get("data", [])
                if uni.get("nome").title() == data.comite.nome.replace("AIESEC em São Paulo Unidade", "")
                                                      .replace("AIESEC em", "")
                                                      .replace("AIESEC no", "")
                                                      .strip().title()
            ),
            None,
        )

        if escritorio_encontrado:
            chave_busca = "gv" if data.produto.id_expa == 7 else "gt"
            valor_bruto = escritorio_encontrado.get(chave_busca, "")

            if valor_bruto == "MC BAZI":
                nome_cl_formatado = "AIESEC no Brasil"
            elif valor_bruto:
                nome_cl_formatado = valor_bruto

    return {
        "nome": str(data.nome).title(),
        "sobrenome": str(data.sobrenome).title(),
        "senha": str(data.senha),
        "dataNascimento": str(data.dataNascimento),
        "programa": int(data.produto.id_expa),
        "nomeCL": nome_cl_formatado
        .replace("AIESEC em São Paulo Unidade", "")
        .replace("AIESEC em", "")
        .replace("AIESEC no", "")
        .strip(),
        "telefone": next((str(t.numero) for t in data.telefone), ""),
        "email": next((str(e.email) for e in data.email), ""),
    }


def payload_atualizar_existe(data: LeadPreCadastroInput) -> Dict[str, Any]:
    """Constrói o payload para atualização no Podio."""
    from app.cache import cache

    id_aiesec_mais_proxima = None
    escritorio_alocado = None

    if data.universidade:
        universidade_encontrada = next(
            (
                uni
                for uni in cache.store.get("divisao-mercado-universidades", {}).get("data", [])
                if uni.get("nome") == data.universidade.nome
            ),
            None,
        )

        if universidade_encontrada:
            chave_busca = "gv" if data.produto.id_expa == 7 else "gt"
            valor_bruto = universidade_encontrada.get(chave_busca, "")
            escritorio_alocado = "AIESEC no Brasil" if valor_bruto == "MC BAZI" else valor_bruto

    elif data.comite:
        escritorio_encontrado = next(
            (
                uni
                for uni in cache.store.get("divisao-mercado-escritorios", {}).get("data", [])
                if uni.get("nome").title() == data.comite.nome.replace("AIESEC em São Paulo Unidade", "")
                                                      .replace("AIESEC em", "")
                                                      .replace("AIESEC no", "")
                                                      .strip().title()
            ),
            None,
        )

        if escritorio_encontrado:
            chave_busca = "gv" if data.produto.id_expa == 7 else "gt"
            valor_bruto = escritorio_encontrado.get(chave_busca, "")
            escritorio_alocado = "AIESEC no Brasil" if valor_bruto == "MC BAZI" else valor_bruto

    if escritorio_alocado:
        id_escritorio_alocado = next(
            (
                u
                for uni in cache.store.get("metadados_card-ogx", {}).get("data", [{}])
                if uni.get("external_id") == "aiesec-mais-proxima"
                for u in uni.get("options", [])
                if u.get("text", "")
                   .replace("AIESEC em São Paulo Unidade", "")
                   .replace("AIESEC em", "")
                   .replace("AIESEC no", "")
                   .strip().title()
                   == escritorio_alocado.replace("AIESEC em São Paulo Unidade", "").replace("AIESEC no", "").replace("AIESEC em", "").strip().title()
            ),
            None,
                   )

        if id_escritorio_alocado:
            id_aiesec_mais_proxima = id_escritorio_alocado.get("id")

    id_final_aiesec = id_aiesec_mais_proxima

    payload: Dict[str, Any] = {
        "fields": {
            "email": [{"type": str(e.tipo.value), "value": str(e.email)} for e in data.email],
            "telefone": [{"type": str(t.tipo.value), "value": str(t.numero)} for t in data.telefone],
            "produto": int(data.produto.id_podio),
            "aiesec-mais-proxima": id_final_aiesec,
            "status": 1,
        },
        "tags": [],
    }

    if data.universidade:
        payload["fields"]["universidade"] = str(data.universidade.nome)
    if data.tag:
        payload["tags"] = data.tag if isinstance(data.tag, list) else [str(data.tag)]

    return payload


def payload_qualificacao_lead(data: QualificacaoLead) -> Dict[str, Any]:
    """Constrói o payload de qualificação do lead."""
    payload: Dict[str, Any] = {"fields": {}}
    payload_fields = payload["fields"]

    if data.curso:
        payload_fields["qual-seu-curso"] = formatar_texto(str(data.curso))
    if data.idiomas:
        payload_fields["possui-outro-idioma"] = [i.id for i in data.idiomas]
    if data.semestreCurso:
        payload_fields["qual-seu-semestre"] = int(data.semestreCurso.id)
    if data.areaAtuacao:
        payload_fields["qual-sua-area-de-atuacao"] = int(data.areaAtuacao.id)
    if data.nivelAtuacao:
        payload_fields["qual-seu-nivel-de-atuacao"] = int(data.nivelAtuacao.id)

    return payload


def payload_anexar_arquivo_podio(data: QualificacaoLead) -> Dict[str, Any]:
    """Constrói o payload para vincular arquivo ao Podio."""
    return {
        "ref_type": "item",
        "ref_id": data.item_id,
    }


__all__ = [
    "payload_pre_cadastro_podio",
    "payload_expa",
    "payload_atualizar_existe",
    "payload_qualificacao_lead",
    "payload_anexar_arquivo_podio",
]