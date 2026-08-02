"""Handler customizado para erros de validação do OpenAPI3 no Flask.

Intercepta as exceções de esquema/payload disparadas pelo Flask-OpenAPI3,
normaliza a estrutura através do utilitário `resolve_exception` e encapsula
o retorno em um objeto de resposta Flask HTTP válido com código de status apropriado.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from flask import jsonify, make_response  # Utilitários nativos do Flask para serialização JSON e construção de Response
from .resolve import resolve_exception  # Funções de resolução e mapeamento de exceções para DTOs
from ..dto import AppError

# =================================================================
# 2. HANDLER DE ERROS DE VALIDAÇÃO
# =================================================================

def handle_validation_error(e: Exception):
    """Trata erros de validação disparados pela extensão Flask-OpenAPI3.

    Args:
        e (Exception): A exceção de validação capturada pelo middleware da API.

    Returns:
        Response: Objeto de resposta oficial do Flask contendo o JSON de erro
        formatado e o status code HTTP correspondente.
    """
    # 1. Resolve a exceção convertendo-a para um DTO de erro padronizado
    erro_resolvido = resolve_exception(e)

    # 2. Extrai o dicionário serializado do modelo Pydantic e o status code HTTP
    response_body = erro_resolvido.model_dump()
    status_code = erro_resolvido.status_code

    # 3. Converte o dicionário em JSON e encapsula na Response do Flask para evitar falhas no abort()
    return make_response(jsonify(response_body), status_code)

def handle_app_error(error: AppError):
    """Retorna o erro no formato pydantic"""
    dto = error.dto # pegar o erro no formato da class base do dto
    return dto.model_dump(), dto.status_code.value # converte para um dict

# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["handle_validation_error","handle_app_error"]