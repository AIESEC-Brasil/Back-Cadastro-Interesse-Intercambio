"""
Módulo de Infraestrutura: AIESEC Security - Cache Layer.

Gerenciamento de cache em memória (RAM) utilizando o padrão Cache-Aside.
Este módulo evita chamadas repetitivas a serviços externos, respeitando um
tempo de vida (TTL) configurado globalmente ou customizado por chamada.

Pode ser usado tanto como classe singleton clássica (`await cache.get_or_set(...)`)
quanto como decorador de rota assíncrona do Flask (`@cache(key="...", baixando="...")`).
"""

# ==============================
# Importações (Dependencies)
# ==============================
import logging                      # Sistema de registros para monitoramento
import inspect                      # Suporte ao event loop e detecção de corotinas
import asyncio                      # Sincronização assíncrona não-bloqueante (asyncio.Lock)
from dataclasses import dataclass, field # Facilita a criação de classes de estrutura de dados
from functools import wraps         # Preserva metadados de funções decoradas
from flask import jsonify, request  # Serializador JSON e objeto de requisição do Flask
from typing import (
    Any,                            # Tipo flexível para aceitar diversos formatos de dados
    Callable,                       # Tipo para funções passadas como argumento (callbacks)
    Dict,                           # Definição de dicionários tipados
    Tuple,                          # Definição de tuplas para retorno (status, data)
    Optional                        # Permite indicar que um parâmetro pode ser nulo/opcional
)

from ..config import CACHE_TTL      # Tempo limite (em segundos) definido no ambiente global
from ..utils.resolve import (
    resolve_response                # Garante o tratamento de retornos de forma assíncrona
)
from ..utils.data import (
    agora_timestamp,                # Função para obter tempo atual (Horário de São Paulo)
)
from ..dto import HttpStatus        # Enum com os Status Http

# =================================================================
# CONFIGURAÇÕES DE LOGGING
# =================================================================
logger = logging.getLogger(__name__)

# =================================================================
# CONSTANTES DE CACHE
# =================================================================
FIELDS_PERMITIDOS = {
    "qual-semestre-do-curso",
    "qual-sua-area-de-atuacao",
    "qual-seu-nivel-de-atuacao",
    "possui-outro-idioma",
    "produto",
    "aiesec-mais-proxima",
    "tag-origem-2",
    "tag-meio-2-2",
    "status",
    "produto"
}

# =================================================================
# GERENCIADOR DE CACHE (CLASS E DECORADOR HÍBRIDO ASSÍNCRONO)
# =================================================================
@dataclass
class CacheManager:
    """
    Controla o ciclo de vida de dados voláteis armazenados em memória de forma não-bloqueante.

    Suporta uso clássico imperativo assíncrono ou uso declarativo através de decoradores de rotas.
    Utiliza asyncio.Lock para serializar a gravação de forma cooperativa sem congelar a aplicação.
    """

    store: Dict[str, Dict[str, Any]] = field(default_factory=dict, init=False)

    # Mapeia dinamicamente os locks para cada Event Loop de requisição ativa
    # Isso evita o erro: 'RuntimeError: Lock is bound to a different event loop'
    _locks: Dict[asyncio.AbstractEventLoop, asyncio.Lock] = field(default_factory=dict, init=False)

    async def get_or_set(
            self,
            key: str,
            baixando: str,
            fetch: Optional[Callable[[], Any]] = None,
            resync: bool = False,
            CACHE_TTL: int = CACHE_TTL
    ) -> Tuple[Any, int]:
        """
        Executa a estratégia clássica Cache-Aside utilizando sincronização assíncrona.
        """
        now = agora_timestamp()

        # 1. Obtém dinamicamente o loop de eventos que está tratando esta thread/requisição
        loop = asyncio.get_running_loop()

        # 2. Garante que exista um Lock exclusivo associado a este loop ativo
        if loop not in self._locks:
            self._locks[loop] = asyncio.Lock()

        current_lock = self._locks[loop]

        # --- 3. CENÁRIO: CACHE HIT (Leitura inicial ultra rápida sem lock) ---
        if key in self.store and not resync:
            item = self.store[key]
            if now - item["timestamp"] < CACHE_TTL:
                logger.info(f"AIESEC Cache | HIT: '{baixando}' recuperado da memória.")
                return jsonify(item["data"]), HttpStatus.OK

        # Se não há fetch fornecido e deu cache miss, evitamos toda a lógica de resolve_response
        if fetch is None:
            logger.warning(f"AIESEC Cache | MISS: '{baixando}' não encontrado e nenhuma função 'fetch' foi fornecida para atualização.")
            return jsonify({"error": f"Dados de '{baixando}' não estão em cache."}), HttpStatus.NOT_FOUND

        # --- 4. BLOQUEIO ASSÍNCRONO (Não-bloqueante para o Event Loop ativo) ---
        # Se outra requisição no mesmo loop já estiver atualizando o cache, esta aguarda de forma cooperativa
        async with current_lock:

            # Double check: Verifica se a tarefa que acabou de liberar o lock já atualizou o cache
            if key in self.store and not resync:
                item = self.store[key]
                if now - item["timestamp"] < CACHE_TTL:
                    logger.info(f"AIESEC Cache | HIT (Post-Lock): '{baixando}' resolvido após concorrência.")
                    return jsonify(item["data"]), HttpStatus.OK

            if resync:
                logger.info(f"AIESEC Cache | FORCED RESYNC: Forçando atualização de '{baixando}'...")
            else:
                logger.info(f"AIESEC Cache | MISS: '{baixando}' expirado ou novo. Sincronizando com a fonte...")

            # Resolve a busca externa (pode ser síncrona ou assíncrona)
            if inspect.iscoroutinefunction(fetch):
                result = await fetch()
            else:
                result = fetch()

            # --- TRATAMENTO DINÂMICO E SEGURO DO RETORNO ---
            # 1. Caso retorne uma tupla contendo (status, data)
            if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], int):
                status, raw_data = result
                # Se os dados dentro da tupla precisarem ser resolvidos de forma assíncrona
                if inspect.iscoroutine(raw_data):
                    status, data = await resolve_response(raw_data)
                else:
                    status = HttpStatus.OK
                    data = raw_data
            else:
                # 2. Caso retorne apenas dados brutos ou uma Promise que resolve direto no dado
                status = HttpStatus.OK
                if inspect.iscoroutine(result):
                    # Se o resolve_response retornar uma tupla (status, dados), extraímos corretamente
                    resolved = await resolve_response(result)
                    if isinstance(resolved, tuple) and len(resolved) == 2 and isinstance(resolved[0], int):
                        status, data = resolved
                    else:
                        status = HttpStatus.OK
                        data = resolved
                else:
                    status = HttpStatus.OK
                    data = result

            # Filtra apenas os campos permitidos
            if isinstance(data, dict) and data.get("fields"):
                new_fields = []
                for field_data in data["fields"]:
                    if field_data.get("external_id") in FIELDS_PERMITIDOS:
                        opts = field_data.get("config", {}).get("settings", {}).get("options", [])
                        new_fields.append({
                            "external_id": field_data["external_id"],
                            "options": [o for o in opts if o.get("status") == "active"]
                        })
                data = new_fields

            # Grava no dicionário de memória (operação síncrona e atômica)
            self.store[key] = {
                "data": data,
                "timestamp": now,
            }

        logger.info(f"AIESEC Security | Sincronização de '{baixando}' concluída com sucesso!")
        return jsonify(data), status


# ==============================
# Singleton (Instância Única)
# ==============================
cache = CacheManager()

# ==============================
# Exportações do Módulo
# ==============================
__all__ = ['cache']