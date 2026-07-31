"""Router Module (router.py).

Extensão customizada do APIBlueprint para padronização de rotas e documentação.
Este componente é o que permite a geração automática da documentação Swagger (OpenAPI).
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from typing import Optional  # Suporte para digitação de tipos opcionais

from flask_openapi3 import APIBlueprint  # Blueprint estendido do Flask com OpenAPI3


# =================================================================
# 2. CLASSE ROUTER (CUSTOM BLUEPRINT)
# =================================================================

class Router(APIBlueprint):
    """Especialização do APIBlueprint para o ecossistema da aplicação.

    Ao utilizar esta classe, todas as rotas registradas herdarão:
    - Prefixo de URL consistente.
    - Validação automática de schemas de resposta (validate_response=True).
    - Integração direta com a documentação OpenAPI/Swagger.
    """

    def __init__(
            self,
            name: Optional[str] = None,
            url_prefix: str = "",
    ) -> None:
        """Inicializa o Router customizado herdando as funcionalidades do APIBlueprint.

        Args:
            name (Optional[str]): Nome identificador do Blueprint. Se omitido, assume __name__.
            url_prefix (str): Prefixo de URL que antecede todas as rotas registradas neste grupo.
        """
        # Inicializa a classe pai (APIBlueprint)
        # Passamos o nome do blueprint, o nome do módulo atual (__name__)
        # e o prefixo que todas as rotas deste grupo utilizarão.
        super().__init__(
            name or __name__,  # Nome identificador do Blueprint
            __name__,          # Nome do pacote/módulo de importação
            url_prefix=url_prefix,
            # Força a API a validar se o retorno da rota condiz com o DTO/schema documentado
            validate_response=True,
            )


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["Router"]