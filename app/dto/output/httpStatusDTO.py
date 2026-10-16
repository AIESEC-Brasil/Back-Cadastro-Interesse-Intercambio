from enum import IntEnum                                   # Base para criação de enumeradores de inteiros


class HttpStatus(IntEnum):
    """
    Enum completo de Status HTTP oficiais (100–599).

    Baseado nos registros da IANA e nas RFCs atuais (RFC 9110 e relacionadas).

    Categorias:
        1xx → Informacional
        2xx → Sucesso
        3xx → Redirecionamento
        4xx → Erro do Cliente
        5xx → Erro do Servidor

    Uso recomendado:
        HttpStatus.OK
        HttpStatus.NOT_FOUND
        HttpStatus.INTERNAL_SERVER_ERROR

    Vantagem:
        Mais legível e seguro do que usar números "mágicos" como 200, 404, 500.
    """

    # ============================================================
    # 1xx - Informacional
    # Indica que a requisição foi recebida e o processamento continua.
    # ============================================================

    CONTINUE = 100  # Cliente deve continuar enviando a requisição
    SWITCHING_PROTOCOLS = 101  # Servidor está trocando o protocolo
    PROCESSING = 102  # Servidor recebeu e está processando (WebDAV)
    EARLY_HINTS = 103  # Indica cabeçalhos preliminares antes da resposta final


    # ============================================================
    # 2xx - Sucesso
    # Indica que a requisição foi recebida, entendida e aceita com sucesso.
    # ============================================================

    OK = 200  # Requisição bem-sucedida
    CREATED = 201  # Recurso criado com sucesso
    ACCEPTED = 202  # Requisição aceita para processamento futuro
    NON_AUTHORITATIVE_INFORMATION = 203  # Informação modificada por proxy
    NO_CONTENT = 204  # Sucesso sem conteúdo de resposta
    RESET_CONTENT = 205  # Cliente deve resetar o formulário
    PARTIAL_CONTENT = 206  # Resposta parcial (range)
    MULTI_STATUS = 207  # Múltiplos status (WebDAV)
    ALREADY_REPORTED = 208  # Já reportado anteriormente (WebDAV)
    IM_USED = 226  # Instância manipulada usada


    # ============================================================
    # 3xx - Redirecionamento
    # Indica que ação adicional é necessária para completar a requisição.
    # ============================================================

    MULTIPLE_CHOICES = 300  # Múltiplas opções disponíveis
    MOVED_PERMANENTLY = 301  # Recurso movido permanentemente
    FOUND = 302  # Recurso movido temporariamente
    SEE_OTHER = 303  # Ver outro recurso via GET
    NOT_MODIFIED = 304  # Recurso não foi modificado (cache)
    USE_PROXY = 305  # Deve usar proxy (obsoleto)
    TEMPORARY_REDIRECT = 307  # Redirecionamento temporário
    PERMANENT_REDIRECT = 308  # Redirecionamento permanente


    # ============================================================
    # 4xx - Erro do Cliente
    # Indica erro causado pelo cliente (requisição inválida).
    # ============================================================

    BAD_REQUEST = 400  # Requisição malformada
    UNAUTHORIZED = 401  # Autenticação necessária
    PAYMENT_REQUIRED = 402  # Reservado para uso futuro
    FORBIDDEN = 403  # Cliente autenticado, mas sem permissão
    NOT_FOUND = 404  # Recurso não encontrado
    METHOD_NOT_ALLOWED = 405  # Método HTTP não permitido
    NOT_ACCEPTABLE = 406  # Tipo de resposta não aceitável
    PROXY_AUTHENTICATION_REQUIRED = 407  # Autenticação via proxy necessária
    REQUEST_TIMEOUT = 408  # Tempo limite da requisição excedido
    CONFLICT = 409  # Conflito de estado (ex: duplicidade)
    GONE = 410  # Recurso removido permanentemente
    LENGTH_REQUIRED = 411  # Cabeçalho Content-Length necessário
    PRECONDITION_FAILED = 412  # Pré-condição falhou
    PAYLOAD_TOO_LARGE = 413  # Corpo da requisição muito grande
    URI_TOO_LONG = 414  # URI muito longa
    UNSUPPORTED_MEDIA_TYPE = 415  # Tipo de mídia não suportado
    RANGE_NOT_SATISFIABLE = 416  # Intervalo inválido
    EXPECTATION_FAILED = 417  # Expectativa não atendida
    IM_A_TEAPOT = 418  # Easter egg oficial (RFC 2324)
    MISDIRECTED_REQUEST = 421  # Requisição direcionada incorretamente
    UNPROCESSABLE_ENTITY = 422  # Erro semântico (validação)
    LOCKED = 423  # Recurso bloqueado (WebDAV)
    FAILED_DEPENDENCY = 424  # Falha em dependência anterior
    TOO_EARLY = 425  # Requisição muito antecipada
    UPGRADE_REQUIRED = 426  # Cliente deve mudar protocolo
    PRECONDITION_REQUIRED = 428  # Pré-condição obrigatória
    TOO_MANY_REQUESTS = 429  # Limite de requisições excedido (rate limit)
    REQUEST_HEADER_FIELDS_TOO_LARGE = 431  # Cabeçalhos muito grandes
    UNAVAILABLE_FOR_LEGAL_REASONS = 451  # Bloqueado por razões legais


    # ============================================================
    # 5xx - Erro do Servidor
    # Indica falha interna no servidor.
    # ============================================================

    INTERNAL_SERVER_ERROR = 500  # Erro genérico no servidor
    NOT_IMPLEMENTED = 501  # Funcionalidade não implementada
    BAD_GATEWAY = 502  # Falha em gateway/proxy
    SERVICE_UNAVAILABLE = 503  # Servidor indisponível
    GATEWAY_TIMEOUT = 504  # Timeout em gateway
    HTTP_VERSION_NOT_SUPPORTED = 505  # Versão HTTP não suportada
    VARIANT_ALSO_NEGOTIATES = 506  # Negociação inválida
    INSUFFICIENT_STORAGE = 507  # Armazenamento insuficiente
    LOOP_DETECTED = 508  # Loop detectado
    NOT_EXTENDED = 510  # Extensão necessária
    NETWORK_AUTHENTICATION_REQUIRED = 511  # Autenticação de rede necessária

__all__ = ["HttpStatus"]