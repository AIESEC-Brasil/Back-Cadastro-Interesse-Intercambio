"""
router.py
---------

Extensão customizada do APIBlueprint para padronização de rotas e documentação.
Este componente é o que permite a geração automática do Swagger (OpenAPI).
"""

# ==============================
# Importações (Dependencies)
# ==============================
# O Flask-OpenAPI3 substitui o Blueprint padrão do Flask, adicionando 
# suporte nativo para validação de esquemas e documentação interativa.
from flask_openapi3 import APIBlueprint

# Importa o tipo Callable do nosso módulo global para tipagem estática
from typing import Callable


# =================================================================
# CLASSE ROUTER (CUSTOM BLUEPRINT)
# =================================================================


class Router(APIBlueprint):
    """
    Especialização do APIBlueprint para o ecossistema da aplicação.

    Ao usar esta classe, todas as rotas registradas herdarão:
    - Prefixo de URL consistente.
    - Validação automática de respostas (validate_response=True).
    - Integração direta com a documentação OpenAPI/Swagger.
    """

    def __init__(self, name: str | None = None, url_prefix: str = ""):
        # Inicializa a classe pai (APIBlueprint).
        # passamos o nome do blueprint, o nome do módulo atual (__name__) 
        # e o prefixo que todas as rotas deste grupo usarão.
        super().__init__(
            name or __name__,  # Nome identificador do Blueprint
            __name__,  # Nome do pacote/módulo de importação
            url_prefix=url_prefix,
            # Força a API a validar se o que está sendo retornado condiz 
            # com o esquema (DTO) definido na documentação.
            validate_response=True
        )


# ==============================
# Exportações do Módulo
# ==============================
__all__ = ["Router"]