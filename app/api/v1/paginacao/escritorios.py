# Módulos nativos e extensões do ecossistema Flask para manipulação de requisições e respostas JSON
from flask import request, jsonify

# Conversor assíncrono para executar funções assíncronas de forma síncrona no ecossistema Flask
from asgiref.sync import async_to_sync

# Classe customizada do projeto para gerenciamento e agrupamento de rotas (Blueprint/Router)
from app.controller import Router

# Modelos do SQLAlchemy que representam as tabelas 'DivisaoCL' e 'Universidades' no Banco de Dados
from app.model import DivisaoCL

# Classe ou Enum que padroniza os códigos de status HTTP do projeto (Ex: HttpStatus.OK = 200)
from app.dto import HttpStatus, ListagemEscritoriosRespostaDTOCL, DivisaoMercadoCl

# Instância global do sistema de cache assíncrono do projeto
from app.cache import cache

# Inicialização do módulo de rotas para escritórios com prefixo raiz limpo
escritorios = Router(name="escritorios", url_prefix="")


def _processar_listagem_escritorios(filtros):
    """
    Mecanismo centralizador de busca, filtragem e paginação de escritórios.
    """
    # -------------------------------------------------------------------------
    # 1. VALIDAÇÃO E CONFIGURAÇÃO DA PAGINAÇÃO (Query Params)
    # -------------------------------------------------------------------------
    try:
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=20, type=int)
    except ValueError:
        return jsonify({"erro": "Parâmetros 'page' e 'limit' devem ser inteiros."}), HttpStatus.BAD_REQUEST

    if limit > 100:
        limit = 100
    if limit < 1:
        limit = 20

    query = DivisaoCL.query

    # -------------------------------------------------------------------------
    # 2. APLICAÇÃO DOS FILTROS DE BUSCA
    # -------------------------------------------------------------------------
    nome = filtros.get('nome')
    busca = filtros.get("busca")

    if nome:
        query = query.filter(DivisaoCL.nome == nome)

    if busca:
        query = query.filter(DivisaoCL.nome.ilike(f"%{busca}%"))

    # -------------------------------------------------------------------------
    # 3. TRATAMENTO DA ORDENAÇÃO DINÂMICA
    # -------------------------------------------------------------------------
    sort_by = filtros.get('sort_by', 'id')
    order = filtros.get('order', 'asc')

    sort_columns = {
        'id': DivisaoCL.id,
        'nome': DivisaoCL.nome,
        "Voluntario Global": DivisaoCL.gv,
        "Talento Global": DivisaoCL.gt,
    }

    coluna_ordenacao = sort_columns.get(sort_by, DivisaoCL.id)

    if order.lower() == 'desc':
        query = query.order_by(coluna_ordenacao.desc())
    else:
        query = query.order_by(coluna_ordenacao.asc())

    # -------------------------------------------------------------------------
    # 4. EXECUÇÃO DA PAGINAÇÃO NO BANCO DE DADOS
    # -------------------------------------------------------------------------
    paginated_data = query.paginate(page=page, per_page=limit, error_out=False)

    # -------------------------------------------------------------------------
    # 5. CONSTRUÇÃO DO PAYLOAD ENXUTO (Mapeamento DTO)
    # -------------------------------------------------------------------------
    escritorios_lista = []
    for escritorio in paginated_data.items:
        escritorios_lista.append({
            "id": escritorio.id,
            "nome": escritorio.nome,
            "Voluntario Global": escritorio.gv,
            "Talento Global": escritorio.gt,
        })

    # -------------------------------------------------------------------------
    # 6. RETORNO DE ACORDO COM O REQUISITADO (Status primeiro, depois os Dados)
    # -------------------------------------------------------------------------
    return HttpStatus.OK, {
        "data": escritorios_lista,
        "pagination": {
            "current_page": paginated_data.page,
            "limit": paginated_data.per_page,
            "total_items": paginated_data.total,
            "total_pages": paginated_data.pages,
            "has_next": paginated_data.has_next,
            "has_prev": paginated_data.has_prev
        }
    }


@escritorios.post("/escritorios")
def lista_escritorios_post():
    """
    Buscador de escritórios e alocações de mercado (POST).
    """
    filtros = request.get_json(silent=True) or {}
    chave_dinamica = f"escritorios_post:{request.full_path}:{str(filtros)}"

    response_data,status_code = async_to_sync(cache.get_or_set)(
        key=chave_dinamica,
        fetch=lambda: _processar_listagem_escritorios(filtros),
        baixando="Divisão de mercado dos Escritorios da AIESEC"
    )

    # 1. Recupera os dados de dentro da tupla armazenada no cache (na posição index 1)
    dados_cache = cache.store[chave_dinamica]["data"]
    lista_original = dados_cache["data"]
    paginacao = dados_cache["pagination"]

    # 2. Instancia o DTO passando a lista original para o argumento 'cl'
    lista_tratada = DivisaoMercadoCl(cl=lista_original).model_dump(by_alias=True)

    # 3. Monta o objeto no formato esperado pela raiz do DTO final
    response = {
        "data": lista_tratada,
        "pagination": paginacao
    }

    # 4. Valida no DTO principal, faz o dump respeitando os aliases e retorna com jsonify
    return jsonify(ListagemEscritoriosRespostaDTOCL(**response).model_dump(by_alias=True)), HttpStatus.OK


@escritorios.get("/escritorios", responses={200: ListagemEscritoriosRespostaDTOCL})
def lista_escritorios_get():
    """
    Buscador de escritórios e alocações de mercado (GET).
    """
    filtros = {
        'nome': request.args.get('nome'),
        'busca': request.args.get('busca'),
        'sort_by': request.args.get('sort_by', 'id'),
        'order': request.args.get('order', 'asc')
    }

    chave_dinamica = f"escritorios_get:{request.full_path}"

    response_data,status_code = async_to_sync(cache.get_or_set)(
        key=chave_dinamica,
        fetch=lambda: _processar_listagem_escritorios(filtros),
        baixando="Divisão de mercado dos Escritorios da AIESEC"
    )

    # 1. Recupera os dados de dentro da tupla armazenada no cache (na posição index 1)
    dados_cache = cache.store[chave_dinamica]["data"]
    lista_original = dados_cache["data"]
    paginacao = dados_cache["pagination"]

    # 2. Instancia o DTO passando a lista original para o argumento 'cl'
    lista_tratada = DivisaoMercadoCl(cl=lista_original).model_dump(by_alias=True)

    # 3. Monta o objeto no formato esperado pela raiz do DTO final
    response = {
        "data": lista_tratada,
        "pagination": paginacao
    }

    # 4. Valida no DTO principal e faz o dump respeitando os aliases
    return ListagemEscritoriosRespostaDTOCL(**response).model_dump(by_alias=True), HttpStatus.OK


__all__ = ["escritorios"]