"""Contratos de dados organizados por entrada, integração e persistência.

Fluxo principal do cadastro:
``CriarPreCadastroLead`` -> ``PayloadExpa`` -> ``LeadPersistencia``.
"""

# ==============================================================================
# AGRUPAMENTOS E EXPORTAÇÕES PÚBLICAS
# ==============================================================================
from . import exception, input, integration, output, persistence, types
from .integration import PayloadExpa
from .input import (
    AtualizarPreCadastroLead,
    CriarPreCadastroLead,
    LeadPreCadastroInput,
    QualificacaoLead,
)
from .persistence import LeadPersistencia
from .types import (
    AreaAtuacao,
    Autorizacao,
    CategoriaContato,
    Comite,
    ContatoEmail,
    ContatoTelefone,
    DataNascimento,
    EmailItem,
    Idioma,
    LeadPreCadastroBase,
    Meio,
    NivelAtuacao,
    Origem,
    ProdutoLead,
    Produto,
    ReferenciaLead,
    Senha,
    SemestreCurso,
    Tag,
    TelefoneItem,
    UploadItem,
    Universidade,
)
from .exception import AppError, BaseErrorResponse, ErrorDetail, ValidationErrorResponse
from .output import (
    ConflitoEmail,
    ConflitoTelefone,
    ConflitosLeadOutput,
    HttpStatus,
    LeadPreCadastroOutput,
    Metadados,
    RetornoGenerico,
)

__all__ = [
    "input",
    "output",
    "exception",
    "integration",
    "persistence",
    "types",
    "LeadPreCadastroBase",
    "Metadados",
    "HttpStatus",
    "LeadPreCadastroInput",
    "CriarPreCadastroLead",
    "AtualizarPreCadastroLead",
    "QualificacaoLead",
    "AppError",
    "BaseErrorResponse",
    "ErrorDetail",
    "ValidationErrorResponse",
    "Autorizacao",
    "AreaAtuacao",
    "CategoriaContato",
    "Comite",
    "ContatoEmail",
    "ContatoTelefone",
    "DataNascimento",
    "EmailItem",
    "Idioma",
    "Meio",
    "NivelAtuacao",
    "Origem",
    "PayloadExpa",
    "ProdutoLead",
    "Produto",
    "ReferenciaLead",
    "Senha",
    "SemestreCurso",
    "Tag",
    "TelefoneItem",
    "Universidade",
    "UploadItem",
    "LeadPreCadastroOutput",
    "LeadPersistencia",
    "RetornoGenerico",
    "ConflitoEmail",
    "ConflitoTelefone",
    "ConflitosLeadOutput",
]
