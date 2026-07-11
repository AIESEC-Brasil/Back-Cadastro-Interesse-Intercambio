"""
Módulo de Infraestrutura: AIESEC Security - Cache Layer.

Gerenciamento de cache em memória (RAM) utilizando o padrão Cache-Aside.
Este módulo evita chamadas repetitivas a serviços externos, respeitando um
tempo de vida (TTL) configurado globalmente.
"""

# ==============================
# Importações (Dependencies)
# ==============================
import logging                      # Sistema de registros para monitoramento
from dataclasses import dataclass    # Facilita a criação de classes de estrutura de dados
from flask import (
    jsonify,                        # Serializador JSON para respostas HTTP
)
from typing import (
    Any,                            # Tipo flexível para aceitar diversos formatos de dados
    Callable,                       # Tipo para funções passadas como argumento (callbacks)
    Dict,                           # Definição de dicionários tipados
    Tuple                           # Definição de tuplas para retorno (status, data)
)
from threading import Lock          # Mecanismo de sincronização para evitar concorrência por chave
from ..config import CACHE_TTL      # Tempo limite (em segundos) definido no ambiente global
from ..utils import (
    agora_timestamp,                # Função para obter tempo atual (Horário de São Paulo)
    resolve_response                # Garante o tratamento de retornos síncronos ou assíncronos
)

from app.repository import buscar_todas_universidades, buscar_todos_cl  # Funções de acesso a dados persistidos
# =================================================================
# CONFIGURAÇÕES DE LOGGING
# =================================================================

logger = logging.getLogger(__name__)

# =================================================================
# GERENCIADOR DE CACHE
# =================================================================

@dataclass
class CacheManager:
    """
    Controla o ciclo de vida de dados voláteis armazenados em memória.
    """

    def __init__(self):
        """Inicializa o repositório central de cache e os controladores de concorrência."""
        # Armazena os dados brutos e seus respectivos timestamps de criação.
        self.store: Dict[str, Dict[str, Any]] = {}
        
        # Mantém um Lock exclusivo para cada chave de cache ativa.
        self.locks: Dict[str, Lock] = {}
        
        # Lock Mestre (Garante consistência atômica ao criar novos sub-locks)
        self.master_lock = Lock()

    def get_lock(self, key: str) -> Lock:
        """
        Retorna ou cria de forma síncrona/atômica um Lock exclusivo para uma chave.
        """
        with self.master_lock:
            if key not in self.locks:
                self.locks[key] = Lock()
            return self.locks[key]

    def get_or_set(self, key: str, fetch: Callable[[], Tuple[Any, int]], baixando: str):
        """
        Executa a estratégia Cache-Aside. Se os dados estiverem válidos, retorna o cache (HIT).
        Caso contrário, busca os dados na fonte e atualiza a memória (MISS).

        Args:
            key (str): Identificador único do recurso no cache.
            fetch (Callable): Função de fallback para buscar os dados se o cache falhar.
            baixando (str): Nome descritivo do recurso para logs de auditoria.

        Returns:
            Response: Objeto JSON formatado e o status HTTP correspondente.
        """

        # now: Captura o timestamp atual em segundos para validar a expiração.
        now = agora_timestamp()

        # --- 1. CENÁRIO: CACHE HIT (Sucesso na Memória) ---
        if key in self.store:
            item = self.store[key]

            if now - item["timestamp"] < CACHE_TTL:
                logger.info(f"AIESEC Cache | HIT: '{baixando}' recuperado da memória.")
                return jsonify(item["data"]), 200

        # lock: Obtém o mecanismo de sincronização exclusivo da chave solicitada.
        lock = self.get_lock(key)

        # --- BLOCO CRÍTICO PROTEGIDO ---
        # Apenas uma thread por vez pode executar este trecho para a mesma chave.
        with lock:

            # Double check: Revalida o cache após adquirir o Lock,
            # pois outra requisição pode já ter atualizado os dados.
            if key in self.store:
                item = self.store[key]
                if now - item["timestamp"] < CACHE_TTL:
                    logger.info(f"AIESEC Cache | HIT (Post-Lock): '{baixando}' recuperado após sincronização.")
                    return jsonify(item["data"]), 200

            # --- 2. CENÁRIO: CACHE MISS (Inexistente ou Expirado) ---
            logger.info(f"AIESEC Cache | MISS: '{baixando}' expirado ou novo. Sincronizando com a fonte...")

            result = fetch()

            status, data = resolve_response(result)
            data = [
                    {
                        "external_id": field["external_id"],
                        "options": [
                            option
                            for option in field["config"]["settings"]["options"]
                            if option["status"] == "active"
                        ]
                    }
                    for field in data["fields"]
                    if field["external_id"] in [
                        "qual-semestre-do-curso",
                        "qual-sua-area-de-atuacao",
                        "qual-seu-nivel-de-atuacao",
                        "possui-outro-idioma",
                        "produto",
                        "aiesec-mais-proxima",
                        "tag-origem-2",
                        "tag-meio-2-2"
                    ]
                ] if data.get("fields") else data
            # --- 3. PERSISTÊNCIA E ATUALIZAÇÃO ---
            self.store[key] = {
                "data": data,  # Armazena apenas os campos relevantes do payload
                "timestamp": now,
                "cl": [cl.to_dict() for cl in buscar_todos_cl()],
                "universidades": [u.to_dict() for u in buscar_todas_universidades()]
            }

            logger.info(f"AIESEC Security | Sincronização de '{baixando}' concluída com sucesso!")

            return jsonify(data), status


# ==============================
# Singleton (Instância Única)
# ==============================

cache = CacheManager()

# ==============================
# Exportações
# ==============================
__all__ = ['cache']