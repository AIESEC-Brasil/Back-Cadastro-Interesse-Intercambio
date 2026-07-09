"""
Configuração de Inicialização
-----------------------------

Este módulo prepara o ambiente global da aplicação, injetando utilitários
de validação e expondo a fábrica da aplicação.
"""

# ==============================
# Importações (Dependencies)
# ==============================
import builtins  # Módulo que fornece acesso direto a todos os identificadores 'embutidos' do Python
from pydantic import validate_call  # Decorador do Pydantic que verifica tipos de dados em tempo de execução

# ==============================
# Injeção Global (Monkey Patching)
# ==============================

# Injeta o decorador 'validate_call' no escopo global do Python sob o nome 'validar'
# Isso permite usar @validar em qualquer arquivo do projeto sem precisar importar o Pydantic
builtins.validar = validate_call

# ==============================
# Exportação da Fábrica
# ==============================

# Importa a função de criação da aplicação definida no módulo principal
from app.main import create_app

# Define quais símbolos serão exportados quando este pacote for importado via 'from ... import *'
__all__ = [
    "create_app"
]