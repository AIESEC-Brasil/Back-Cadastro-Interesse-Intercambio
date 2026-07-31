"""Funções utilitárias de formatação de nomes e construção de URLs.

- Remoção de acentos e capitalização de nomes (Title Case).
- Limpeza de conectores e partículas gramaticais para geração de e-mails/IDs.
- Formatação mantendo acentuação gráfica original.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import re  # Expressões regulares para divisão e limpeza de strings
from typing import List, Tuple  # Tipagem para listas e tuplas de retorno
from urllib.parse import urlencode  # Utilitário para conversão de dicionários em query strings
import unicodedata  # Manipulação e decomposição de caracteres Unicode


# =================================================================
# 2. PROCESSAMENTO DE NOMES
# =================================================================

@validar
def formatar_nome(nome: str) -> str:
    """Remove acentos de uma string e aplica capitalização (Title Case).

    O processo utiliza a normalização NFD para decompor caracteres de seus
    acentos e filtra apenas os caracteres base.

    Args:
        nome (str): A string original contendo o nome.

    Returns:
        str: Nome sem acentos, com cada palavra iniciando em maiúscula.
    """
    # Decompõe caracteres acentuados (caractere base + acento) e descarta os diacríticos (Mn)
    nome_sem_acentos: str = "".join(
        c for c in unicodedata.normalize("NFD", nome)
        if unicodedata.category(c) != "Mn"
    )

    # Divide a string, capitaliza cada pedaço e junta novamente com um único espaço
    return " ".join(p.capitalize() for p in nome_sem_acentos.split())


@validar
def formatar_nome_com_acentos(nome: str) -> str:
    """Padroniza a capitalização do nome mantendo os acentos originais.

    Args:
        nome (str): Nome a ser formatado.

    Returns:
        str: Nome com espaços limpos e palavras capitalizadas.
    """
    # Remove espaços excedentes nas extremidades e entre as palavras
    nome_limpo: str = " ".join(nome.strip().split())

    # Capitaliza cada palavra preservando a acentuação original
    return " ".join(p.capitalize() for p in nome_limpo.split())


@validar
def limpar_palavras(nome: str, sobrenome: str) -> Tuple[List[str], List[str]]:
    """Filtra conectores e partículas gramaticais para preparação de e-mails/IDs.

    Remove elementos como "de", "da" ou vogais soltas que não agregam valor
    em identificadores de usuários.

    Args:
        nome (str): Nome do usuário.
        sobrenome (str): Sobrenome do usuário.

    Returns:
        Tuple[List[str], List[str]]: Tupla contendo (nomes_filtrados, sobrenomes_filtrados).
    """
    # Termos e artigos irrelevantes para a composição de identificadores
    conectores: List[str] = ["de", "da", "di", "do", "du"]
    vogais_soltas: List[str] = ["a", "e", "i", "o", "u"]

    # Converte para minúsculo, divide por espaços e filtra conectores e vogais soltas
    nomes: List[str] = [
        formatar_nome(p) for p in re.split(r"\s+", nome.lower().strip())
        if p not in conectores and p not in vogais_soltas
    ]

    # Processa os sobrenomes aplicando a mesma regra de filtragem
    sobrenomes: List[str] = [
        formatar_nome(p) for p in re.split(r"\s+", sobrenome.lower().strip())
        if p not in conectores and p not in vogais_soltas
    ]

    return nomes, sobrenomes


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = [
    "formatar_nome",
    "formatar_nome_com_acentos",
    "limpar_palavras",
]