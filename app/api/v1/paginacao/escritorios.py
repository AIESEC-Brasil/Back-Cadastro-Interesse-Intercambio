"""Módulo de Rotas e Paginação de Escritórios (CLs) - AIESEC Gateway.

Fornece endpoints GET e POST para consulta, filtragem e paginação dinâmica
dos Comitês Locais (CLs / Escritórios) da AIESEC, com suporte a cache transparente
e padronização de respostas via DTOs.
"""

# ==============================================================================
# 1. IMPORTAÇÕES DA BIBLIOTECA PADRÃO E ECOSSISTEMA FLASK
# ==============================================================================

# Conversor assíncrono para executar funções async de forma síncrona no Flask
from asgiref.sync import async_to_sync

# Recursos do Flask para captura do contexto de requisição e geração de JSON
from flask import jsonify, request

# ==============================================================================
# 2. IMPORTAÇÕES INTERNAS DA APLICAÇÃO
# ==============================================================================

# Gerenciador de cache assíncrono em memória
from app.cache import cache

# DTOs e Enums de status HTTP para validação e serialização de dados
from app.dto import (
    DivisaoMercadoCl,
    HttpStatus,
    ListagemEscritoriosRespostaDTOCL,
)

# Modelo SQLAlchemy para acesso à tabela DivisaoCL
from app.model import DivisaoCL

# Roteador customizado da aplicação
from app.router import Router

# ==============================================================================
# 3. CONFIGURAÇÃO DO ROTEADOR
# ==============================================================================

# Inicializa o roteador de escritórios com prefixo raiz limpo
escritorios = Router(name="escritorios", url_prefix="")


# ==============================================================================
# 4. FUNÇÕES AUXILIARES E REGRA DE NEGÓCIO
# ==============================================================================

def _processar_listagem_escritorios(filtros: dict):
    """Mecanismo centralizador de busca, filtragem e paginação de escritórios.

    Args:
        filtros (dict): Dicionário contendo os parâmetros de busca (nome,
          busca, sort_by, order).

    Returns:
        Tuple[HttpStatus, dict]: Tupla contendo o status HTTP e a estrutura
        paginada dos dados recuperados do banco de dados.
    """
    # -------------------------------------------------------------------------
    # 4.1 Validação dos Parâmetros de Paginação (Query Params)
    # -------------------------------------------------------------------------
    try:
        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=20, type=int)
    except ValueError:
        return (
            jsonify({"erro": "Parâmetros 'page' e 'limit' devem ser inteiros."}),
            HttpStatus.BAD_REQUEST,
        )

    # Limites de segurança para evitar sobrecarga na paginação
    if limit > 100:
        limit = 100
    if limit < 1:
        limit = 20

    # Inicialização da query SQLAlchemy
    query = DivisaoCL.query

    # -------------------------------------------------------------------------
    # 4.2 Aplicação dos Filtros de Busca
    # -------------------------------------------------------------------------
    nome = filtros.get("nome")
    busca = filtros.get("busca")

    if nome:
        query = query.filter(DivisaoCL.nome == nome)

    if busca:
        query = query.filter(DivisaoCL.nome.ilike(f"%{busca}%"))

    # -------------------------------------------------------------------------
    # 4.3 Tratamento da Ordenação Dinâmica
    # -------------------------------------------------------------------------
    sort_by = filtros.get("sort_by", "id")
    order = filtros.get("order", "asc")

    sort_columns = {
        "id": DivisaoCL.id,
        "nome": DivisaoCL.nome,
        "Voluntario Global": DivisaoCL.gv,
        "Talento Global": DivisaoCL.gt,
    }

    coluna_ordenacao = sort_columns.get(sort_by, DivisaoCL.id)

    if order.lower() == "desc":
        query = query.order_by(coluna_ordenacao.desc())
    else:
        query = query.order_by(coluna_ordenacao.asc())

    # -------------------------------------------------------------------------
    # 4.4 Execução da Paginação no Banco de Dados
    # -------------------------------------------------------------------------
    paginated_data = query.paginate(page=page, per_page=limit, error_out=False)

    # -------------------------------------------------------------------------
    # 4.5 Construção do Payload Enxuto
    # -------------------------------------------------------------------------
    escritorios_lista = []
    for escritorio in paginated_data.items:
        escritorios_lista.append(
            {
                "id": escritorio.id,
                "nome": escritorio.nome,
                "Voluntario Global": escritorio.gv,
                "Talento Global": escritorio.gt,
            }
        )

    # -------------------------------------------------------------------------
    # 4.6 Retorno do Resultado Padrão (Status + Dados)
    # -------------------------------------------------------------------------
    return HttpStatus.OK, {
        "data": escritorios_lista,
        "pagination": {
            "current_page": paginated_data.page,
            "limit": paginated_data.per_page,
            "total_items": paginated_data.total,
            "total_pages": paginated_data.pages,
            "has_next": paginated_data.has_next,
            "has_prev": paginated_data.has_prev,
        },
    }


# ==============================================================================
# 5. ENDPOINTS DA API (POST & GET)
# ==============================================================================

@escritorios.post("/escritorios")
def lista_escritorios_post():
    """Buscador de escritórios e alocações de mercado (método POST).

    Permite o envio de filtros avançados no corpo da requisição JSON,
    com suporte a armazenamento em cache dinâmico.
    """
    filtros = request.get_json(silent=True) or {}
    chave_dinamica = f"escritorios_post:{request.full_path}:{str(filtros)}"

    # Tenta recuperar os dados do cache ou executa o callback de busca
    response_data, status_code = async_to_sync(cache.get_or_set)(
        key=chave_dinamica,
        fetch=lambda: _processar_listagem_escritorios(filtros),
        baixando="Divisão de mercado dos Escritorios da AIESEC",
    )

    # 1. Recupera os dados armazenados na estrutura de cache
    dados_cache = cache.store[chave_dinamica]["data"]
    lista_original = dados_cache["data"]
    paginacao = dados_cache["pagination"]

    # 2. Instancia o DTO convertendo a lista original para o alias esperado
    lista_tratada = DivisaoMercadoCl(cl=lista_original).model_dump(by_alias=True)

    # 3. Estrutura o payload de resposta final
    response = {"data": lista_tratada, "pagination": paginacao}

    # 4. Valida no DTO principal e retorna o JSON formatado
    return (
        jsonify(
            ListagemEscritoriosRespostaDTOCL(**response).model_dump(
                by_alias=True
            )
        ),
        HttpStatus.OK,
    )


@escritorios.get(
    "/escritorios", responses={200: ListagemEscritoriosRespostaDTOCL}
)
def lista_escritorios_get():
    """Buscador de escritórios e alocações de mercado (método GET).

    Recebe parâmetros de busca e ordenação diretamente da URL (Query Params).
    """
    filtros = {
        "nome": request.args.get("nome"),
        "busca": request.args.get("busca"),
        "sort_by": request.args.get("sort_by", "id"),
        "order": request.args.get("order", "asc"),
    }

    chave_dinamica = f"escritorios_get:{request.full_path}"

    # Tenta recuperar os dados do cache ou executa o callback de busca
    response_data, status_code = async_to_sync(cache.get_or_set)(
        key=chave_dinamica,
        fetch=lambda: _processar_listagem_escritorios(filtros),
        baixando="Divisão de mercado dos Escritorios da AIESEC",
    )

    # 1. Recupera os dados armazenados no cache
    dados_cache = cache.store[chave_dinamica]["data"]
    lista_original = dados_cache["data"]
    paginacao = dados_cache["pagination"]

    # 2. Converte a lista utilizando o DTO especializado
    lista_tratada = DivisaoMercadoCl(cl=lista_original).model_dump(by_alias=True)

    # 3. Monta o objeto final de resposta
    response = {"data": lista_tratada, "pagination": paginacao}

    # 4. Valida no DTO principal e retorna o dicionário serializável
    return (
        ListagemEscritoriosRespostaDTOCL(**response).model_dump(by_alias=True),
        HttpStatus.OK,
    )


# ==============================================================================
# 6. EXPORTAÇÃO CONSOLIDADA E CONTRATO PÚBLICO
# ==============================================================================

__all__ = [
    "escritorios",  # Roteador consolidado contendo os endpoints de escritórios
]