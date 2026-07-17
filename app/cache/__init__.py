"""
cache
-----

Pacote de cache em memória com timestamps no horário de Recife.
Inclui a classe CacheManager e a instância global 'cache'.
"""

# =================================================================
# Importações de Infraestrutura
# =================================================================

# Importa a instância singleton 'cache' já inicializada do módulo base.
# Isso garante que todas as partes da aplicação compartilhem o mesmo dicionário de memória.
from .cache import cache

# =================================================================
# Exportação Consolidada
# =================================================================

#

# O __all__ limita a exposição apenas à instância 'cache'.
# Dessa forma, evita-se que a classe CacheManager seja instanciada
# acidentalmente em outros lugares, o que criaria caches isolados e
# quebraria a lógica de persistência temporária global.
__all__ = [
    "cache"
]