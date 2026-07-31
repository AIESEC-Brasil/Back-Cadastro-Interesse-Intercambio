"""Configuração de Inicialização do Pacote Principal.

Este módulo prepara o ambiente global da aplicação, injetando utilitários
de validação em tempo de execução no escopo do interpretador Python (`builtins`)
e expondo a fábrica principal da aplicação Flask.
"""

# =================================================================
# 1. IMPORTAÇÕES E INJEÇÃO GLOBAL
# =================================================================
import builtins  # Módulo nativo que dá acesso aos identificadores embutidos do Python

from pydantic import validate_call  # Decorador do Pydantic para validação de tipos de dados em funções/métodos

# Injeta o decorador 'validate_call' diretamente no escopo global do Python como 'validar'
# Permite usar o decorador `@validar` em qualquer arquivo do projeto sem importações adicionais
builtins.validar = validate_call

# =================================================================
# 2. IMPORTAÇÃO E EXPORTAÇÃO DA FÁBRICA
# =================================================================
# Importa a função factory de criação do aplicativo a partir do módulo principal
from app.main import create_app

# Define explicitamente as exportações públicas da raiz do pacote `app`
__all__ = ["create_app"]