"""Helpers de formatação específicos da camada de apresentação/integração.

Atualmente contém utilitário para empacotar dados no formato esperado pela
API do Podio (chaves dentro do nó 'fields').
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from typing import Any, Dict  # Utilitários de tipagem para dicionários flexíveis


# =================================================================
# 2. FORMATADORES DE INTEGRAÇÃO COM A API DO PODIO
# =================================================================

def payload_podio(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Constrói o payload padrão esperado pela API REST do Podio.

    Encapsula o dicionário de campos dentro da chave raiz 'fields'.

    Args:
        data (Dict[str, Any]): Dicionário contendo os ID/mapeamentos de campos do Podio.

    Returns:
        Dict[str, Dict[str, Any]]: Estrutura formatada no padrão {"fields": data}.
    """
    return {"fields": data}


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["payload_podio"]