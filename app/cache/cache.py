"""Módulo de Infraestrutura de Cache - AIESEC Security.

Este módulo implementa uma camada de gerenciamento de cache em memória RAM
utilizando a arquitetura "Cache-Aside" (Lazy Loading) com sincronização
assíncrona não-bloqueante.

O objetivo principal é interceptar requisições repetitivas a serviços externos
(como a API do Podio), reduzindo o tempo de latência da aplicação e evitando
bloqueios do Event Loop em ambientes web assíncronos ou multi-thread (Flask/Gunicorn).
"""

# ==============================================================================
# 1. IMPORTAÇÕES DA BIBLIOTECA PADRÃO E DE TERCEIROS
# ==============================================================================

# O módulo asyncio fornece a infraestrutura para concorrência cooperativa via Event Loop
import asyncio

# O módulo inspect é utilizado para introspecção de objetos em tempo de execução
# (ex: verificar se uma função é corotina antes de usar o operador 'await')
import inspect

# O sistema de logging padrão do Python é usado para rastreabilidade e auditoria
import logging

# O decorator @dataclass automatiza a criação do método __init__ e estruturas de dados
from dataclasses import dataclass, field

# Tipos abstratos fornecidos pelo módulo typing para anotação estática de código (Mypy)
from typing import (
    Any,        # Indica que um valor pode ser de qualquer tipo
    Callable,   # Anotação para funções ou métodos passados como argumentos (callbacks)
    Dict,       # Tipo dicionário Python
    Optional,   # Indica que um parâmetro pode ser do tipo especificado ou None
    Tuple,      # Tipo tupla (usado para retornos múltiplos como status e payload)
)

# O utilitário jsonify do Flask formata dicionários Python em objetos HTTP Response com MIME JSON
from flask import jsonify

# ==============================================================================
# 2. IMPORTAÇÕES DE MÓDULOS INTERNOS DA APLICAÇÃO
# ==============================================================================

# Importa o Tempo de Vida padrão (Time To Live) definido nas configurações da aplicação
from ..config import CACHE_TTL

# Enum que encapsula os códigos de status HTTP padrão (ex: HttpStatus.OK = 200)
from ..dto import HttpStatus

# Utilitário que retorna o timestamp Unix atual ajustado para o fuso horário local
from ..utils.data import agora_timestamp

# Helper responsável por resolver Promises/Coroutines e extrair o conteúdo real de respostas
from ..utils.resolve import resolve_response

# ==============================================================================
# 3. CONFIGURAÇÃO DE LOGS E CONSTANTES GLOBAIS
# ==============================================================================

# Cria uma instância do logger associada ao nome deste módulo específico (__name__)
logger = logging.getLogger(__name__)

# Conjunto (Set) contendo os IDs externos dos campos que têm permissão para serem
# armazenados no cache e expostos aos clientes da API. Isso garante a higienização
# e segurança dos dados recebidos do Podio.
FIELDS_PERMITIDOS = {
    "qual-semestre-do-curso",
    "qual-sua-area-de-atuacao",
    "qual-seu-nivel-de-atuacao",
    "possui-outro-idioma",
    "produto",
    "aiesec-mais-proxima",
    "tag-origem-2",
    "tag-meio-2-2",
    "email",
    "telefone"
}


# ==============================================================================
# 4. CLASSE GERENCIADORA DE CACHE (CACHE MANAGER)
# ==============================================================================

@dataclass
class CacheManager:
    """Gerenciador centralizado de cache em memória com controle de concorrência.

    Esta classe armazena pares de chave-valor em memória RAM (self.store) e
    gerencia o ciclo de vida dos dados, expirando-os conforme o TTL estipulado.
    """

    # Armazenamento em memória: Dicionário onde a chave é o ID do recurso (str)
    # e o valor é outro dicionário contendo o 'data' (payload) e 'timestamp' (tempo da gravação).
    # O campo init=False impede que esse parâmetro seja exigido na instanciação da classe.
    store: Dict[str, Dict[str, Any]] = field(default_factory=dict, init=False)

    # Dicionário de Locks por Event Loop:
    # O Python em ambientes assíncronos pode criar múltiplos Event Loops (um por thread do Flask).
    # Como um asyncio.Lock é vinculado estritamente ao loop em que foi criado, este dicionário
    # mapeia cada Event Loop ativo para seu próprio Lock correspondente, prevenindo o erro:
    # "RuntimeError: Lock is bound to a different event loop".
    _locks: Dict[asyncio.AbstractEventLoop, asyncio.Lock] = field(
        default_factory=dict, init=False
    )

    async def get_or_set(
            self,
            key: str,
            baixando: str,
            fetch: Optional[Callable[[], Any]] = None,
            resync: bool = False,
            ttl: int = CACHE_TTL - 3600,
    ) -> Tuple[Any, int]:
        """Recupera um dado do cache ou executa a função de busca (Cache-Aside).

        Args:
            key (str): Chave identificadora única do item no dicionário em memória.
            baixando (str): Descrição legível usada exclusivamente nos logs do sistema.
            fetch (Optional[Callable]): Função ou Corotina a ser invocada caso ocorra CACHE MISS.
            resync (bool): Se True, ignora o cache existente e força uma nova busca na API externa.
            ttl (int): Tempo limite de validade do dado armazenado (em segundos) por padrão pe valor de ambiente com folga de 1 h.

        Returns:
            Tuple[Any, int]: Uma tupla contendo o objeto de resposta Flask (JSON) e o Status HTTP.
        """
        # Captura o instante de tempo atual em segundos desde o Unix Epoch
        now = agora_timestamp()

        # ----------------------------------------------------------------------
        # ETAPA 1: Identificação e Mapeamento do Event Loop Atual
        # ----------------------------------------------------------------------
        # Obtém o Loop de Eventos assíncrono que está executando a thread presente
        loop = asyncio.get_running_loop()

        # Verifica se já existe um Lock de sincronização associado ao loop atual.
        # Se não existir, instancia um novo Lock e salva no mapeamento interno da classe.
        if loop not in self._locks:
            self._locks[loop] = asyncio.Lock()

        # Armazena a referência do Lock que controlará o acesso concorrente nesta thread
        current_lock = self._locks[loop]

        # ----------------------------------------------------------------------
        # ETAPA 2: Validação de Leitura Rápida (CACHE HIT - Fase Não-Bloqueante)
        # ----------------------------------------------------------------------
        # Se a chave existe na memória e a flag 'resync' NÃO foi ativada:
        if key in self.store and not resync:
            item = self.store[key]
            # Subtrai o timestamp atual pelo timestamp de criação do item.
            # Se a diferença for menor que o TTL estipulado, o dado ainda é válido!
            if now - item["timestamp"] < ttl:
                logger.info(
                    f"AIESEC Cache | HIT: '{baixando}' recuperado da memória."
                )
                # Retorna os dados convertidos para JSON e com status 200 (OK) sem tocar no Lock
                return jsonify(item["data"]), HttpStatus.OK

        # ----------------------------------------------------------------------
        # ETAPA 3: Tratamento para Ausência da Função de Busca (Fetch)
        # ----------------------------------------------------------------------
        # Se a requisição resultou em Cache Miss (ou expirou) e nenhuma função 'fetch' foi informada,
        # é impossível buscar os dados da fonte original. Retorna erro 404 imediatamente.
        if fetch is None:
            logger.warning(
                f"AIESEC Cache | MISS: '{baixando}' não encontrado e "
                f"nenhuma função 'fetch' foi fornecida para atualização."
            )
            return (
                jsonify({"error": f"Dados de '{baixando}' não estão em cache."}),
                HttpStatus.NOT_FOUND,
            )

        # ----------------------------------------------------------------------
        # ETAPA 4: Bloqueio Assíncrono e Resolução do Cache Miss (Seção Crítica)
        # ----------------------------------------------------------------------
        # Garante que, se 10 requisições simultâneas tentarem acessar o mesmo recurso expirado,
        # apenas A PRIMEIRA executará o bloco abaixo. As outras 9 aguardarão assincronamente a liberação do Lock.
        async with current_lock:

            # --- Padrão Double-Checked Locking (Checagem Dupla após o Lock) ---
            # Quando as outras 9 requisições forem liberadas uma por uma pelo Lock, elas
            # re-verificam o cache. Como a 1ª requisição já terá atualizado a chave, as
            # subsequentes receberão CACHE HIT e não farão chamadas repetidas à API!
            if key in self.store and not resync:
                item = self.store[key]
                if now - item["timestamp"] < ttl:
                    logger.info(
                        f"AIESEC Cache | HIT (Post-Lock): '{baixando}' "
                        f"resolvido após concorrência."
                    )
                    return jsonify(item["data"]), HttpStatus.OK

            # Registro de logs para auditoria no console sobre a origem da sincronização
            if resync:
                logger.info(
                    f"AIESEC Cache | FORCED RESYNC: Forçando atualização de "
                    f"'{baixando}'..."
                )
            else:
                logger.info(
                    f"AIESEC Cache | MISS: '{baixando}' expirado ou novo. "
                    f"Sincronizando com a fonte..."
                )

            # ------------------------------------------------------------------
            # ETAPA 5: Invocação da Função Externa de Busca
            # ------------------------------------------------------------------
            # Utiliza introspecção para verificar se a função 'fetch' é uma corotina (async)
            if inspect.iscoroutinefunction(fetch):
                # Se for async, utiliza o operador 'await' para resolver a Promise de forma não-bloqueante
                result = await fetch()
            else:
                # Se for uma função síncrona tradicional, executa diretamente
                result = fetch()

            # ------------------------------------------------------------------
            # ETAPA 6: Normalização e Tratamento da Resposta Recebida
            # ------------------------------------------------------------------
            # Caso 1: O resultado da busca é uma tupla no formato (status_code, payload)
            if (
                    isinstance(result, tuple)
                    and len(result) == 2
                    and isinstance(result[0], int)
            ):
                status, raw_data = result

                # Se o payload dentro da tupla for uma corotina pendente, resolve-a via helper
                if inspect.iscoroutine(raw_data):
                    status, data = await resolve_response(raw_data)
                else:
                    status = HttpStatus.OK
                    data = raw_data
            else:
                # Caso 2: O resultado é um objeto direto (dicionário ou lista) ou uma Promise pura
                status = HttpStatus.OK

                if inspect.iscoroutine(result):
                    resolved = await resolve_response(result)

                    # Verifica se o resolvedor retornou uma tupla desestruturada
                    if (
                            isinstance(resolved, tuple)
                            and len(resolved) == 2
                            and isinstance(resolved[0], int)
                    ):
                        status, data = resolved
                    else:
                        status = HttpStatus.OK
                        data = resolved
                else:
                    status = HttpStatus.OK
                    data = result

            # ------------------------------------------------------------------
            # ETAPA 7: Filtragem e Sanitização dos Dados (Podio/AIESEC Payload)
            # ------------------------------------------------------------------
            # Se os dados recebidos possuem uma estrutura de campos vindos da API do Podio:
            if isinstance(data, dict) and data.get("fields"):
                new_fields = []

                # Percorre cada campo retornado do banco/API externa
                for field_data in data["fields"]:

                    # Mantém no resultado apenas os campos cujos IDs estejam na lista branca (FIELDS_PERMITIDOS)
                    if field_data.get("external_id") in FIELDS_PERMITIDOS:
                        # 1. Navega com segurança no dicionário para evitar erros caso 'config' ou 'settings' sejam None
                        config = field_data.get("config") or {}
                        settings = config.get("settings") or {}

                        # 2. Busca primeiro a chave "options". Se ela não existir ou estiver vazia,
                        # busca a chave "possible_types". Caso nenhuma exista, usa uma lista vazia []
                        opts = settings.get("options") or settings.get("possible_types") or []

                        # 3. Adiciona os dados processados na lista 'new_fields'
                        new_fields.append({
                            "external_id": field_data["external_id"],
                            "options": [
                                o for o in opts
                                # Mantém o item se:
                                # A) Ele NÃO for dicionário (ex: strings de 'possible_types', aceita diretamente)
                                # B) Ele for dicionário e tiver status "active" ou None (itens de 'options')
                                if not isinstance(o, dict) or o.get("status") in ("active", None)
                            ],
                        })

                # Sobrescreve a variável 'data' apenas com a lista higienizada de campos
                data = new_fields

            # ------------------------------------------------------------------
            # ETAPA 8: Armazenamento Atômico em Memória RAM
            # ------------------------------------------------------------------
            # Salva o resultado tratado e o tempo de criação no dicionário global de memória
            self.store[key] = {
                "data": data,
                "timestamp": now,
            }
        # Emite mensagem de sucesso no log de execução do servidor
        logger.info(
            f"AIESEC Security | Sincronização de '{baixando}' concluída com sucesso!"
        )

        # Retorna a resposta final em formato JSON junto ao código de status HTTP correspondente
        return jsonify(data), status


# ==============================================================================
# 5. INSTANCIAÇÃO DO PATTERN SINGLETON E EXPORTAÇÃO
# ==============================================================================

# Cria uma instância única e global do CacheManager para ser compartilhada em toda a aplicação
cache = CacheManager()

# Declaração estrita dos símbolos expostos ao realizar 'from app.cache import *'
__all__ = [
    "cache",  # Instância Singleton exportada do gerenciador de cache
]