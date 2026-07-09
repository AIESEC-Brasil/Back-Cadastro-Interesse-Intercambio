"""
DTOs de saída e envelopes de resposta para PSEL e integração com Podio.

Inclui enum de HttpStatus, envelope ModelPodio e respostas de pré-cadastro.
"""

# ==============================
# Importações (Dependencies)
# ==============================
from typing import Dict, Any, Optional                     # Tipagem para dicionários e valores opcionais
from pydantic import BaseModel, Field, ConfigDict # Core do Pydantic para validação e esquemas
from .httpstatus import HttpStatus

class ReponsePselPreCadastro(BaseModel):
    """
    Modelo de dados retornado após um pré-cadastro.
    Combina o que foi salvo localmente com o que foi enviado ao CRM.
    """
    # Atributos
    banco_de_dados: Optional[Dict[str, Any]] = Field(default_factory=dict) # Resumo do registro no SQL
    podio: Dict[str,Any] # Cópia do payload enviado/recebido do Podio

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

class ReponseOutPutPreCadastro(ReponsePselPreCadastro):
    """
    Envelope de resposta padrão para o pré-cadastro PSEL.
    Este é o formato final que o front-end receberá.
    """
    # Atributos
    status: str                  # 'success' ou 'error'
    message: str                 # Mensagem amigável para o usuário/desenvolvedor
    status_code: HttpStatus      # Código numérico HTTP (ex: 201)

# ==============================
# Exportações do Módulo
# ==============================
__all__ = [
    "ReponseOutPutPreCadastro",
    "HttpStatus"
]