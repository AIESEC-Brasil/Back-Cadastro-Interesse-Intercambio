"""
Helpers de formatação específicos da camada de apresentação/integração.

Atualmente contém utilitários para empacotar e transformar dados de DTOs
no formato esperado pelas APIs REST do Podio (chaves dentro do nó 'fields')
e da plataforma EXPA.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from datetime import date, datetime
from typing import Any, Dict  # Utilitários de tipagem para dicionários flexíveis

# Módulos de DTOs para validação e estruturação dos dados
from ..dto import (
    CategoriaContato,
    CriarPreCadastroLead,
    DataNascimento,
    LeadPreCadastroInput,
    LeadPreCadastroOutput,
)


# =================================================================
# 2. FORMATADORES DE INTEGRAÇÃO COM A API DO PODIO E EXPA
# =================================================================

def payload_pre_cadastro_podio(data: LeadPreCadastroInput) -> dict[
    str, dict[str | Any, int | str | list[dict[str, CategoriaContato | str]] | DataNascimento | Any] | list[Any]]:
    """Constrói o payload padrão esperado pela API REST do Podio para pré-cadastro.

    Encapsula o dicionário de campos dentro da chave raiz 'fields' e formata
    os dados de contato, produtos, comitê e autorizações.

    Args:
        data (LeadPreCadastroInput): Objeto DTO contendo os dados validados do pré-cadastro.

    Returns:
        dict: Estrutura formatada no padrão esperado pelo Podio contendo 'fields' e 'tags'.
    """
    payload = {
        "fields": {
            "title": data.nome.__str__().title(),
            "sobrenome-2": data.sobrenome.__str__().title(),
            "email": [{"type": e.tipo.value.__str__(), "value": e.email.__str__()} for e in data.email],
            "telefone": [{"type": t.tipo.value.__str__(), "value": t.numero.__str__()} for t in data.telefone],
            "data-de-nascimento-2": data.dataNascimento.__str__(),
            "produto": data.produto.id_podio.__int__(),
            "aiesec-mais-proxima": data.comite.id.__int__(),
            "tag-origem-2": data.origem.id.__int__(),
            "status-expa": 1,
            "eu-concordo-com-a-coleta-e-uso-dos-meus-dados-conforme-": data.autorizacao.__int__()
        },
        "tags": []
    }

    # Atribuições condicionais de campos opcionais
    if data.universidade: payload["fields"]["universidade"] = data.universidade.nome.__str__()
    if data.meio: payload["fields"]["tag-meio-2-2"] = data.meio.id.__int__()
    if data.tag: payload["tags"] = data.tag if isinstance(data.tag, list) else [data.tag.__str__()]

    return payload


def payload_expa(data: CriarPreCadastroLead) -> Dict[str, Any]:
    """Formata e constrói o payload necessário para a integração com a API do EXPA.

    Esta função extrai e transforma os dados do DTO de pré-cadastro do lead,
    preparando a estrutura de dicionário aceita para a criação de conta no EXPA.

    Args:
        data (CriarPreCadastroLead): Objeto DTO contendo as informações validadas
            do formulário de pré-cadastro.

    Returns:
        Dict[str, Any]: Dicionário contendo os dados formatados para envio ao EXPA.

    Details:
        - Os campos `nome` e `sobrenome` são formatados em Title Case (`.title()`).
        - O campo `nomeCL` é sanitizado para remover variações de prefixos do nome do comitê.
        - Os campos `telefone` e `email` utilizam `next()` com fallback para evitar erros
          em caso de listas de contato vazias.
    """
    payload = {
        "nome": data.nome.__str__().title(),
        "sobrenome": data.sobrenome.__str__().title(),
        "senha": data.senha.__str__(),
        "dataNascimento": data.dataNascimento.__str__(),
        "programa": data.produto.id_expa.__int__(),
        "nomeCL": data.comite.nome.__str__()
        .replace("AIESEC em São Paulo Unidade", "")
        .replace("AIESEC em", "")
        .replace("AIESEC no", "")
        .strip(),
        "telefone": next((t.numero.__str__() for t in data.telefone), ""),
        "email": next((e.email.__str__() for e in data.email), ""),
    }
    return payload


def payload_atualizar_existe(data: LeadPreCadastroInput) -> Dict[str, Any]:
    """Constrói o payload para atualização de um lead já existente na plataforma Podio.

    Mapeia e atualiza os dados de contato (e-mail e telefone), programa de interesse,
    comitê local responsável e status do EXPA no nó 'fields', além de tratar campos opcionais.

    Args:
        data (LeadPreCadastroOutput): Objeto DTO contendo os dados do lead existente
            a serem atualizados.

    Returns:
        Dict[str, Any]: Estrutura formatada com a chave 'fields' e 'tags' pronta para o Podio.
    """
    payload: Dict[str, Any] = {
        "fields": {
            "email": [{"type": e.tipo.value.__str__(), "value": e.email.__str__()} for e in data.email],
            "telefone": [{"type": t.tipo.value.__str__(), "value": t.numero.__str__()} for t in data.telefone],
            "produto": data.produto.id_podio.__int__(),
            "aiesec-mais-proxima": data.comite.id.__int__(),
            "status": 1
        },
        "tags": []
    }

    # Atribuições condicionais de campos opcionais
    if data.universidade: payload["fields"]["universidade"] = data.universidade.nome.__str__()
    if data.tag: payload["tags"] = data.tag if isinstance(data.tag, list) else [data.tag.__str__()]

    return payload


# =================================================================
# 3. EXPORTAÇÃO CONSOLIDADA DO MÓDULO
# =================================================================
__all__ = [
    "payload_pre_cadastro_podio",
    "payload_expa",
    "payload_atualizar_existe",
]