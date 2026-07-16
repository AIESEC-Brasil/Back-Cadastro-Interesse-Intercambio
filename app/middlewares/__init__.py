"""
Middlewares Module
------------------

Centraliza as camadas de interceptação da aplicação.
Organiza a segurança, autenticação de serviços externos e auditoria de rotas.
"""

# ==============================
# Importações de Interceptores
# ==============================

# 1. Segurança de Infraestrutura: Valida se quem chama a API tem permissão (IP/Domínio)
from .auth import verificar_origem

# 2. Integração com Terceiros: Garante que o token do Podio esteja pronto para o serviço
from .token_routes import gerar_token_podio_rota

# 3. Observabilidade: Registra os logs de acesso e define políticas de cache pós-processamento
from .register_endpoint import register_url

from .whitelist import require_ip_whitelist

# ==============================
# Exportação Consolidada
# ==============================

#

# O __all__ facilita o registro no arquivo principal da aplicação (app.py)
# permitindo o uso de: app.before_request(verificar_origem)
__all__ = [
    "verificar_origem",
    "gerar_token_podio_rota",
    "register_url",
    "require_ip_whitelist"
]