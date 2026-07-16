"""
Módulo de Infraestrutura: AIESEC Security - Cache Layer.

Gerenciamento de cache em memória (RAM) utilizando o padrão Cache-Aside.
Este módulo evita chamadas repetitivas a serviços externos, respeitando um
tempo de vida (TTL) configurado globalmente.

Pode ser usado tanto como classe singleton clássica (`await cache.get_or_set(...)`)
quanto como decorador de rota assíncrona do Flask (`@cache(key="...", baixando="...")`).
"""

# ==============================
# Importações (Dependencies)
# ==============================
import logging                      # Sistema de registros para monitoramento
import inspect                     # Suporte ao event loop e detecção de corotinas
import threading                    # Sincronização segura para threads e loops de eventos distintos
from dataclasses import dataclass, field # Facilita a criação de classes de estrutura de dados
from functools import wraps         # Preserva metadados de funções decoradas
from flask import jsonify, request  # Serializador JSON e objeto de requisição do Flask
from typing import (
    Any,                            # Tipo flexível para aceitar diversos formatos de dados
    Callable,                       # Tipo para funções passadas como argumento (callbacks)
    Dict,                           # Definição de dicionários tipados
    Tuple                           # Definição de tuplas para retorno (status, data)
)

from ..config import CACHE_TTL      # Tempo limite (em segundos) definido no ambiente global
from ..utils import (
    agora_timestamp,                # Função para obter tempo atual (Horário de São Paulo)
    resolve_response                # Garante o tratamento de retornos de forma assíncrona
)
from ..dto import HttpStatus        # Enum com os Status Http
from ..repository import buscar_todas_universidades, buscar_todos_cl  # Funções de acesso a dados
from ..dto import DivisaoMercado

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
    "tag-meio-2-2"
}

# =================================================================
# GERENCIADOR DE CACHE (CLASS E DECORADOR HÍBRIDO ASSÍNCRONO)
# =================================================================
@dataclass
class CacheManager:
    """
    Controla o ciclo de vida de dados voláteis armazenados em memória de forma não-bloqueante.
    Suporta uso clássico imperativo assíncrono ou uso declarativo através de decoradores de rotas.
    """

    store: Dict[str, Dict[str, Any]] = field(default_factory=dict, init=False)

    # Substituído por threading.Lock para garantir isolamento seguro entre loops distintos
    # gerenciados pela thread principal e pelas threads de apoio criadas pelo asgiref
    _global_lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    async def get_or_set(
            self,
            key: str,
            fetch: Callable[[], Any],
            baixando: str,
            metadados: bool = False,
            resync: bool = False,
            CACHE_TTL:int=CACHE_TTL
    ) -> Tuple[Any, int]:
        """
        Executa a estratégia clássica Cache-Aside de maneira assíncrona.
        Se os dados estiverem válidos E resync=False, retorna o cache (HIT).
        Caso contrário, ignora o cache, executa a busca de forma não-bloqueante e atualiza a store (MISS/FORCED).
        """
        now = agora_timestamp()

        # --- 1. CENÁRIO: CACHE HIT (Bypass completo se resync for True) ---
        if key in self.store and not resync:
            item = self.store[key]
            if now - item["timestamp"] < CACHE_TTL:
                logger.info(f"AIESEC Cache | HIT: '{baixando}' recuperado da memória.")
                return jsonify(item["data"]), HttpStatus.OK

        # --- BLOCO CRÍTICO PROTEGIDO POR THREADING LOCK ---
        # Bloqueamos de forma thread-safe apenas para verificar/atualizar estados na store local
        with self._global_lock:
            # Double check: Evita condições de corrida (Race Conditions)
            if key in self.store and not resync:
                item = self.store[key]
                if now - item["timestamp"] < CACHE_TTL:
                    logger.info(f"AIESEC Cache | HIT (Post-Lock): '{baixando}' recuperado após sincronização.")
                    return jsonify(item["data"]), HttpStatus.OK

            # --- 2. CENÁRIO: CACHE MISS OU RESYNC FORÇADO ---
            if resync:
                logger.info(f"AIESEC Cache | FORCED RESYNC: Forçando atualização de '{baixando}'...")
            else:
                logger.info(f"AIESEC Cache | MISS: '{baixando}' expirado ou novo. Sincronizando com a fonte...")

        # Executa a busca real na fonte externa fora do lock para não bloquear outras threads do servidor
        result = fetch()

        # AGUARDA a resolução da resposta de forma assíncrona (I/O livre)
        status, data = await resolve_response(result)

        # Filtra apenas os campos permitidos para otimizar o payload
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

        # --- 3. PERSISTÊNCIA E ATUALIZAÇÃO ---
        with self._global_lock:
            self.store[key] = {
                "data": data,
                "timestamp": now,
            }

            if metadados:
                logger.info(f"AIESEC Security | Sincronizando metadados de roteamento para '{baixando}'...")
                self.store[key]["cl"] = DivisaoMercado.processar_lista(await buscar_todos_cl())
                self.store[key]["universidades"] = DivisaoMercado.processar_lista(await buscar_todas_universidades())
                logger.info(f"AIESEC Security | Metadados de roteamento para '{baixando}' sincronizados com sucesso!")

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