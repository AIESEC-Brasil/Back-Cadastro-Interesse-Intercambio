"""Tipos compartilhados entre os contratos de entrada e saída."""

from .contact import (
    CATEGORIAS_CONTATO_VALIDAS,
    CATEGORIAS_EMAIL_VALIDAS,
    CATEGORIAS_TELEFONE_VALIDAS,
    CategoriaContato,
    ContatoEmail,
    ContatoTelefone,
    EmailItem,
    TelefoneItem,
    listar_categorias_contato_validas,
)
from .lead import (
    AreaAtuacao,
    Autorizacao,
    Comite,
    DataNascimento,
    Idioma,
    Meio,
    NivelAtuacao,
    Origem,
    Produto,
    ProdutoLead,
    ReferenciaLead,
    Senha,
    SemestreCurso,
    Tag,
    Universidade,
    buscar_id_opcao_cache,
    validar_opcao_cache,
    validar_texto_opcao_cache,
)
from .lead_base import LeadPreCadastroBase
from .upload import MAX_PDF_SIZE_BYTES, UploadItem

# ==============================================================================
# TIPOS COMPARTILHADOS
# ==============================================================================
__all__ = [
    "AreaAtuacao",
    "Autorizacao",
    "CATEGORIAS_CONTATO_VALIDAS",
    "CATEGORIAS_EMAIL_VALIDAS",
    "CATEGORIAS_TELEFONE_VALIDAS",
    "CategoriaContato",
    "Comite",
    "ContatoEmail",
    "ContatoTelefone",
    "DataNascimento",
    "EmailItem",
    "Idioma",
    "LeadPreCadastroBase",
    "MAX_PDF_SIZE_BYTES",
    "Meio",
    "NivelAtuacao",
    "Origem",
    "Produto",
    "ProdutoLead",
    "ReferenciaLead",
    "Senha",
    "SemestreCurso",
    "Tag",
    "TelefoneItem",
    "Universidade",
    "UploadItem",
    "buscar_id_opcao_cache",
    "listar_categorias_contato_validas",
    "validar_opcao_cache",
    "validar_texto_opcao_cache",
]
