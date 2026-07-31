"""Pacote de Cache em Memória - AIESEC Security.

Gerenciador de armazenamento volátil em RAM com timestamps ajustados ao fuso
horário local. Inclui a classe CacheManager e expõe a instância global 'cache'.
"""

# =================================================================
# 1. IMPORTAÇÕES DOS COMPONENTES DE CACHE
# =================================================================

# Importa a instância singleton compartilhada do módulo de cache
from .cache import cache


# =================================================================
# 2. EXPORTAÇÃO CONSOLIDADA E CONTRATO PÚBLICO
# =================================================================

# O __all__ expõe o singleton 'cache' para uso direto em rotas e serviços.
# Isso impede a instanciação acidental de múltiplos objetos CacheManager,
# o que quebraria a persistência de dados voláteis na memória RAM.
__all__ = [
    "cache",  # Instância Singleton global do gerenciador de cache
]