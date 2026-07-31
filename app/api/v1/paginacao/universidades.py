"""Módulo de Rotas e Paginação de Universidades - AIESEC Gateway.

Fornece endpoints GET e POST para consulta, filtragem, ordenação dinamicamente
paginada de instituições de ensino superior (Universidades) integradas aos
programas Voluntário Global e Talento Global, com suporte a cache transparente.
"""

# ==============================================================================
# 1. IMPORTAÇÕES DA BIBLIOTECA PADRÃO E ECOSSISTEMA FLASK
# ==============================================================================

# Conversor assíncrono para executar métodos async de forma síncrona no Flask
from asgiref.sync import async_to_sync

# Funções do Flask para captura do contexto da requisição e envio de JSON
from flask import jsonify, request

# ==============================================================================
# 2. IMPORTAÇÕES INTERNAS DO PROJETO
# ==============================================================================

# Gerenciador global de cache em memória/RAM
from app.cache import cache

# DTOs para validação e serialização das respostas HTTP
from app.dto import (
    DivisaoMercadoUniversidades,
    HttpStatus,
    ListagemEscritoriosRespostaDTOUniversidades,
)

# Modelo da tabela 'Universidades' no SQLAlchemy
from app.model import Universidades

# Classe de gerenciamento e agrupamento de rotas
from app.router import Router

# ==============================================================================
# 3. INICIALIZAÇÃO DO ROTEADOR
# ==============================================================================

# Inicializa o roteador exclusivo para os endpoints de universidades
universidades = Router(name="universidades", url_prefix="")


# ==============================================================================
# 4. FUNÇÕES DE SUPORTE E REGRA DE NEGÓCIO
# ==============================================================================

def _processar_listagem_universidades(filtros: dict):
    """Mecanismo centralizador de busca, filtragem e paginação de universidades.

    Args:
        filtros (dict): Dicionário contendo os filtros de busca (nome, busca,
          sort_by, order).

    Returns:
        Tuple[HttpStatus, dict]: Tupla contendo o status HTTP e a estrutura
        paginada dos dados recuperados do banco.
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

    # Aplica limites de segurança na paginação
    if limit > 100:
        limit = 100
    if limit < 1:
        limit = 20

    # Inicia a query SQLAlchemy
    query = Universidades.query

    # -------------------------------------------------------------------------
    # 4.2 Aplicação dos Filtros de Busca
    # -------------------------------------------------------------------------
    nome = filtros.get("nome")
    busca = filtros.get("busca")

    if nome:
        query = query.filter(Universidades.nome == nome)

    if busca:
        query = query.filter(Universidades.nome.ilike(f"%{busca}%"))

    # -------------------------------------------------------------------------
    # 4.3 Tratamento da Ordenação Dinâmica
    # -------------------------------------------------------------------------
    sort_by = filtros.get("sort_by", "id")
    order = filtros.get("order", "asc")

    sort_columns = {
        "id": Universidades.id,
        "nome": Universidades.nome,
        "Voluntario Global": Universidades.gv,
        "Talento Global": Universidades.gt,
    }

    coluna_ordenacao = sort_columns.get(sort_by, Universidades.id)

    if order.lower() == "desc":
        query = query.order_by(coluna_ordenacao.desc())
    else:
        query = query.order_by(coluna_ordenacao.asc())

    # -------------------------------------------------------------------------
    # 4.4 Execução da Paginação no Banco de Dados
    # -------------------------------------------------------------------------
    paginated_data = query.paginate(page=page, per_page=limit, error_out=False)

    # -------------------------------------------------------------------------
    # 4.5 Construção do Payload DTO Enxuto
    # -------------------------------------------------------------------------
    universidades_lista = []
    for univ in paginated_data.items:
        universidades_lista.append(
            {
                "id": univ.id,
                "nome": univ.nome,
                "Voluntario Global": univ.gv,
                "Talento Global": univ.gt,
            }
        )

    # -------------------------------------------------------------------------
    # 4.6 Retorno Padrão (Status HTTP + Dicionário de Dados)
    # -------------------------------------------------------------------------
    return HttpStatus.OK, {
        "data": universidades_lista,
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

@universidades.post("/universidades")
def lista_universidades_post():
    """Buscador e filtro de universidades via requisição POST.

    Permite o envio de filtros avançados no corpo do JSON da requisição,
    utilizando cache dinâmico com base na rota e payload.
    """
    filtros = request.get_json(silent=True) or {}
    chave_dinamica = f"universidades_post:{request.full_path}:{str(filtros)}"

    # Busca no cache ou executa o processamento
    response_data, status_code = async_to_sync(cache.get_or_set)(
        key=chave_dinamica,
        fetch=lambda: _processar_listagem_universidades(filtros),
        baixando="Divisão de mercado de Instituição por mercado da AIESEC",
    )

    # 1. Recupera os dados do armazenamento de cache
    dados_cache = cache.store[chave_dinamica]["data"]
    lista_original = dados_cache["data"]
    paginacao = dados_cache["pagination"]

    # 2. Instancia o DTO convertendo os dados originais
    lista_tratada = DivisaoMercadoUniversidades(
        universidades=lista_original
    ).model_dump(by_alias=True)

    # 3. Estrutura a resposta
    response = {"data": lista_tratada, "pagination": paginacao}

    # 4. Valida e retorna o JSON usando o DTO principal
    return (
        jsonify(
            ListagemEscritoriosRespostaDTOUniversidades(**response).model_dump(
                by_alias=True
            )
        ),
        HttpStatus.OK,
    )


@universidades.get(
    "/universidades",
    responses={200: ListagemEscritoriosRespostaDTOUniversidades},
)
def lista_universidades_get():
    """Buscador e filtro de universidades via consulta GET (Query Params).

    Permite consulta através dos parâmetros de URL com cache dinâmico.
    """
    filtros = {
        "nome": request.args.get("nome"),
        "busca": request.args.get("busca"),
        "sort_by": request.args.get("sort_by", "id"),
        "order": request.args.get("order", "asc"),
    }

    chave_dinamica = f"universidades_get:{request.full_path}"

    # Busca no cache ou executa o processamento
    response_data, status_code = async_to_sync(cache.get_or_set)(
        key=chave_dinamica,
        fetch=lambda: _processar_listagem_universidades(filtros),
        baixando="Divisão de mercado de Instituição por mercado da AIESEC",
    )

    # 1. Recupera os dados do cache
    dados_cache = cache.store[chave_dinamica]["data"]
    lista_original = dados_cache["data"]
    paginacao = dados_cache["pagination"]

    # 2. Transforma a lista através do DTO
    lista_tratada = DivisaoMercadoUniversidades(
        universidades=lista_original
    ).model_dump(by_alias=True)

    # 3. Monta a estrutura da resposta
    response = {"data": lista_tratada, "pagination": paginacao}

    # 4. Retorna a estrutura serializada
    return (
        ListagemEscritoriosRespostaDTOUniversidades(**response).model_dump(
            by_alias=True
        ),
        HttpStatus.OK,
    )


# ==============================================================================
# 6. EXPORTAÇÃO CONSOLIDADA E CONTRATO PÚBLICO
# ==============================================================================

# Corrigido o erro de nome de variável para 'universidades'
__all__ = [
    "universidades",  # Roteador com endpoints de consulta de universidades
]