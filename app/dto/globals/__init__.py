from .divisaoMercadoDTO import *
from .universidadeDTO import Universidade
from .autorizacaoDTO import Autorizacao
from .categoriaContatoDTO import CategoriaContato
from .emailItemDTO import EmailItem
from .telefoneItemDTO import TelefoneItem
from .comiteDTO import Comite
from .dataNascimentoDTO import DataNascimento
from .produtoDTO import Produto
__all__ = (
        divisaoMercadoDTO.__all__ +
        universidadeDTO.__all__ +
        autorizacaoDTO.__all__ +
        categoriaContatoDTO.__all__ +
        emailItemDTO.__all__ +
        telefoneItemDTO.__all__ +
        comiteDTO.__all__ +
        produtoDTO.__all__ +
        dataNascimentoDTO.__all__
)