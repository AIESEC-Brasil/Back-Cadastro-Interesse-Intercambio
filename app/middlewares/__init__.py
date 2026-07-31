"""Módulo de Exportação de Middlewares (Middlewares Package).

Centraliza as camadas de interceptação e governança da aplicação.
Organiza a segurança de infraestrutura, autenticação de serviços externos,
restrição de acesso por IP e auditoria de tráfego.
"""

# =================================================================
# 1. IMPORTAÇÕES DE INTERCEPTORES
# =================================================================

# 1. Segurança de Infraestrutura: Valida permissões de origem (IP/Domínio)
from .autorizacao import verificar_origem

# 2. Segurança de Rota: Restringe acesso via Whitelist de IPs
from .lista_autorizados import require_ip_whitelist

# 3. Observabilidade e Auditoria: Registra logs e injeta cabeçalhos de HTTP Cache
from .registrando_endpoint import register_url

# 4. Integração com Terceiros: Garante o Token de Acesso ao Podio otimizado via cache
from .registrando_token_rota import gerar_token_podio_rota


# =================================================================
# 2. EXPORTAÇÃO CONSOLIDADA VIA __all__
# =================================================================

# O __all__ facilita o registro no arquivo principal da aplicação (app.py)
# permitindo o uso de: app.before_request(verificar_origem)
__all__ = [
    "verificar_origem",
    "gerar_token_podio_rota",
    "register_url",
    "require_ip_whitelist",
]