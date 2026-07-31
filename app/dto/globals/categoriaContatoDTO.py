"""Módulo de Enumeração para Categorias de Contato.

Este módulo define o enumerador `CategoriaContato`, responsável por padronizar
e limitar os tipos/etiquetas de contato (e-mail, telefone, fax) aceitos na
integração com as especificações da API do Podio.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from enum import Enum  # Classe base para criar enumeradores de strings, garantindo conjuntos fixos de opções.


# =================================================================
# 2. ENUMERADOR DE CATEGORIAS DE CONTATO
# =================================================================

class CategoriaContato(str, Enum):
    """Categorias de contato aceitas, padronizadas para integração com o Podio.

    Herda de (str, Enum) para garantir a serialização correta como string no JSON
    e permitir comparações diretas com strings em estruturas condicionais.

    Attributes:
        HOME (str): Representa contatos residenciais ou de escopo puramente pessoal.
        WORK (str): Representa contatos corporativos ou de uso profissional.
        MOBILE (str): Representa linhas telefônicas móveis/celulares.
        MAIN (str): Indica o canal de contato principal do cliente.
        OTHER (str): Categoria genérica para cenários não previstos nas demais chaves.
        PRIVATE_FAX (str): Linha de fax privada de uso pessoal.
        WORK_FAX (str): Linha de fax corporativa de uso comercial.
    """

    HOME = "home"          # Uso residencial/pessoal
    WORK = "work"          # Uso profissional/corporativo
    MOBILE = "mobile"      # Dispositivo móvel/celular
    MAIN = "main"          # Contato principal
    OTHER = "other"        # Outras categorias não listadas
    PRIVATE_FAX = "private_fax"  # Fax pessoal
    WORK_FAX = "work_fax"  # Fax profissional


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["CategoriaContato"]