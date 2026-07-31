"""DTOs (Data Transfer Objects).

Este pacote centraliza todos os contratos de dados da aplicação.
Divide-se em 'input' para validação de requisições e 'output' para
formatação de respostas e integrações, além de módulos para tratamento de exceções
e definições globais.
"""

# =================================================================
# 1. IMPORTAÇÕES DE PACOTES E SUBMÓDULOS
# =================================================================

# Importa os pacotes e submódulos para referência direta via namespace
from . import exception, globals, input, output

# Importa todas as definições expostas do pacote de modelos de entrada (Leads, Parâmetros, etc.)
from .input import *

# Importa todas as definições expostas do pacote de modelos de saída (Status HTTP, Envelopes Podio, etc.)
from .output import *

# Importa todas as definições expostas do submódulo de exceções
from .exception import *

# Importa todas as definições expostas do submódulo de variáveis globais
from .globals import *


# =================================================================
# 2. EXPORTAÇÃO CONSOLIDADA
# =================================================================

# Exposição dos submódulos para permitir acesso direto via namespace
# Exemplo de uso: `from app.dtos import input, output`
__all__ = (
    "input",      # Referência ao pacote de modelos de entrada
    "output",     # Referência ao pacote de modelos de saída
    "exception",  # Referência ao submódulo de tratamento de exceções
    "globals",    # Referência ao submódulo de objetos/constantes globais
)