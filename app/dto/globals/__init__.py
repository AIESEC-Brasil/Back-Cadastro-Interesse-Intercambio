"""Pacote de Módulos e Componentes Reutilizáveis de DTOs.

Centraliza e exporta todas as estruturas básicas de dados, enums e validadores
utilizados na composição dos modelos de entrada e saída do ecossistema.
"""

# =================================================================
# 1. IMPORTAÇÕES DE SUBMÓDULOS E COMPONENTES
# =================================================================

# Importa todas as estruturas expostas do módulo de divisão de mercado
from . import divisaoMercadoDTO
from .divisaoMercadoDTO import *

# Importa o DTO de Universidade e seu módulo
from . import universidadeDTO
from .universidadeDTO import Universidade

# Importa o enumerador de Autorização e seu módulo
from . import autorizacaoDTO
from .autorizacaoDTO import Autorizacao

# Importa o enumerador de Categoria de Contato e seu módulo
from . import categoriaContatoDTO
from .categoriaContatoDTO import CategoriaContato

# Importa o DTO de item de E-mail e seu módulo
from . import emailItemDTO
from .emailItemDTO import EmailItem

# Importa o DTO de item de Telefone e seu módulo
from . import telefoneItemDTO
from .telefoneItemDTO import TelefoneItem

# Importa o DTO de Comitê Local e seu módulo
from . import comiteDTO
from .comiteDTO import Comite

# Importa o DTO de Produto e seu módulo
from . import produtoDTO
from .produtoDTO import Produto

# Importa o DTO de Meio de Contato e seu módulo
from . import meioDTO
from .meioDTO import *

# Importa o DTO de Origem e seu módulo
from . import origemDTO
from .origemDTO import *

# Importa o validador de Data de Nascimento e seu módulo
from . import dataNascimentoDTO
from .dataNascimentoDTO import DataNascimento

# Importa o DTO de Senha e seu módulo
from . import senhaDTO
from .senhaDTO import *

# Importa o DTO de Tag e seu módulo
from . import tagDTO
from .tagDTO import *

# =================================================================
# 2. EXPORTAÇÃO CONSOLIDADA DO PACOTE
# =================================================================

# Concatena o __all__ de cada submódulo para expor a interface pública completa do pacote
__all__ = list(
    divisaoMercadoDTO.__all__
    + universidadeDTO.__all__
    + autorizacaoDTO.__all__
    + categoriaContatoDTO.__all__
    + emailItemDTO.__all__
    + telefoneItemDTO.__all__
    + comiteDTO.__all__
    + produtoDTO.__all__
    + meioDTO.__all__
    + origemDTO.__all__
    + dataNascimentoDTO.__all__
    + senhaDTO.__all__
    + tagDTO.__all__
)