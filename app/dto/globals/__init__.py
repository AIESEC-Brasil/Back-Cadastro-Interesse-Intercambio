"""
Pacote de Módulos e Componentes Reutilizáveis de DTOs (Data Transfer Objects).

Centraliza, re-exporta e unifica todas as estruturas básicas de dados, enumeradores (Enums)
e validadores customizados do Pydantic utilizados na composição dos modelos de entrada (requests)
e saída (responses) do ecossistema.

Este arquivo (__init__.py) permite que os DTOs sejam importados diretamente da raiz do pacote:
    >>> from dtos import UploadItem, Universidade, Autorizacao
"""

# =================================================================================
# 1. IMPORTAÇÕES DE SUBMÓDULOS E COMPONENTES INDIVIDUAIS
# =================================================================================

# Submódulo: Divisão de Mercado
from . import divisaoMercadoDTO
from .divisaoMercadoDTO import *

# Submódulo: Universidade
from . import universidadeDTO
from .universidadeDTO import Universidade

# Submódulo: Autorização (Enumerador de permissões)
from . import autorizacaoDTO
from .autorizacaoDTO import Autorizacao

# Submódulo: Categoria de Contato (Enumerador)
from . import categoriaContatoDTO
from .categoriaContatoDTO import CategoriaContato

# Submódulo: Item de E-mail
from . import emailItemDTO
from .emailItemDTO import EmailItem

# Submódulo: Item de Telefone
from . import telefoneItemDTO
from .telefoneItemDTO import TelefoneItem

# Submódulo: Comitê Local
from . import comiteDTO
from .comiteDTO import Comite

# Submódulo: Produto
from . import produtoDTO
from .produtoDTO import Produto

# Submódulo: Meio de Contato
from . import meioDTO
from .meioDTO import *

# Submódulo: Origem do Contato
from . import origemDTO
from .origemDTO import *

# Submódulo: Validador de Data de Nascimento
from . import dataNascimentoDTO
from .dataNascimentoDTO import DataNascimento

# Submódulo: Estrutura e Validação de Senha
from . import senhaDTO
from .senhaDTO import *

# Submódulo: Tags / Etiquetas
from . import tagDTO
from .tagDTO import *

# Submódulo: Áreas de Atuação Profissional / Acadêmica
from . import areaAtuacaoDTO
from .areaAtuacaoDTO import *

# Submódulo: Idiomas
from . import idiomaDTO
from .idiomaDTO import *

# Submódulo: Níveis de Atuação / Sênioridade
from . import nivelAtuacaoDTO
from .nivelAtuacaoDTO import *

# Submódulo: Semestre Atual do Curso
from . import semestreCursoDTO
from .semestreCursoDTO import *

# Submódulo: Upload de Arquivos / Documentos (Validação de PDF em Base64)
from . import uploadItemDTO
from .uploadItemDTO import *


# =================================================================================
# 2. EXPORTAÇÃO CONSOLIDADA DA INTERFACE PÚBLICA DO PACOTE (__all__)
# =================================================================================

# Concatena dinamicamente as listas `__all__` definidas individualmente em cada submódulo.
# Isso garante que a sintaxe `from dtos import *` exponha exclusivamente os símbolos
# autorizados e mantidos pela API pública do pacote, prevenindo vazamento de escopo.
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
    + areaAtuacaoDTO.__all__
    + idiomaDTO.__all__
    + nivelAtuacaoDTO.__all__
    + semestreCursoDTO.__all__
    + uploadItemDTO.__all__  # Incluído para exportar o UploadItem com validação PDF
)