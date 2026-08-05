"""Helpers de formatação específicos da camada de apresentação/integração.

Atualmente contém utilitário para empacotar dados no formato esperado pela
API do Podio (chaves dentro do nó 'fields').
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from typing import Any, Dict  # Utilitários de tipagem para dicionários flexíveis
from datetime import date, datetime
from ..dto import LeadPreCadastroInput,CategoriaContato, DataNascimento,CriarPreCadastroLead # modulos de dto

# =================================================================
# 2. FORMATADORES DE INTEGRAÇÃO COM A API DO PODIO
# =================================================================

def payload_pre_cadastro_podio(data: LeadPreCadastroInput) -> dict[
    str, dict[str | Any, int | str | list[dict[str, CategoriaContato | str]] | DataNascimento | Any] | list[Any]]:
    """Constrói o payload padrão esperado pela API REST do Podio.

    Encapsula o dicionário de campos dentro da chave raiz 'fields'.

    Args:
        data (Dict[str, Any]): Dicionário contendo os ID/mapeamentos de campos do Podio.

    Returns:
        Dict[str, Dict[str, Any]]: Estrutura formatada no padrão {"fields": data}.
    """
    payload = {
    "fields": {
        "di-ep-id-2": str(121),
        "title": data.nome.__str__().title(),
        "sobrenome-2": data.sobrenome.__str__().title(),
        "email": [{"type":e.tipo.value.__str__(),"value":e.email.__str__()} for e in data.email],
        "telefone": [{"type":t.tipo.value.__str__(),"value":t.numero.__str__()} for t in data.telefone],
        "data-de-nascimento-2": data.dataNascimento.__str__(),
        "produto": data.produto.id_podio.__int__(),
        "aiesec-mais-proxima": data.comite.id.__int__(),
        "tag-origem-2": data.origem.id.__int__(),
        "status-expa": 1,
        "eu-concordo-com-a-coleta-e-uso-dos-meus-dados-conforme-": data.autorizacao.__int__()
    },
    "tags": []
    }
    if data.universidade: payload["fields"]["universidade"] = data.universidade.nome.__str__()
    if data.meio: payload["fields"]["universidade"] = data.meio.id.__int__()
    if data.tag: payload["tags"] = data.tag if isinstance(data.tag,list) else [data.tag.__str__()]
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


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["payload_pre_cadastro_podio","payload_expa"]