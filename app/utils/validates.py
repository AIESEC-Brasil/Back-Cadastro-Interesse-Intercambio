"""Validações utilitárias para entradas de usuário e dados de domínio.

Inclui validações de nomes (com/sem acentos), senhas, e-mails,
telefones (formatos celular e E.164 com +55) e verificação de integridade
de dados de domínio (comitês e produtos) consultando o cache de metadados.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import base64  # Manipulação e validação de dados em codificação base64
from datetime import date, datetime  # Manipulação de objetos de data e hora
import re  # Expressões regulares para correspondência de padrões de texto
from typing import Any, Dict, List  # Tipagem estática para estruturas de dados
import unicodedata  # Normalização Unicode para tratamento de caracteres acentuados

from ..cache import cache  # Instância global do cache da aplicação


# =================================================================
# 2. VALIDAÇÕES DE IDENTIDADE
# =================================================================

@validar
def validar_nome(nome: str) -> bool:
    """Valida se o nome contém apenas letras e espaços, após remover acentuação.

    Args:
        nome (str): String original contendo o nome do usuário.

    Returns:
        bool: True se for um nome válido (alfabético), False caso contrário.
    """
    if not nome:
        return False

    # Normaliza a string em NFD e remove os diacríticos (acentos)
    nome_sem_acentos: str = "".join(
        c for c in unicodedata.normalize("NFD", nome)
        if unicodedata.category(c) != "Mn"
    )

    # Busca por qualquer caractere que NÃO seja letra alfabética ou espaço
    if re.search(r"[^A-Za-z\s]", nome_sem_acentos):
        return False

    # Remove espaços duplicados e verifica se a string resultante não é vazia
    nome_limpo: str = re.sub(r"\s+", " ", nome_sem_acentos).strip()
    return bool(nome_limpo)


@validar
def validar_nome_com_acentos(nome: str) -> bool:
    """Valida nomes permitindo caracteres acentuados do alfabeto latino.

    Args:
        nome (str): Nome a ser validado.

    Returns:
        bool: True se contiver apenas letras (acentuadas ou não) e espaços.
    """
    if not nome:
        return False

    # Remove espaços excedentes no início, fim e entre as palavras
    nome_limpo: str = " ".join(nome.strip().split())

    # Regex para cobrir o intervalo estendido de caracteres latinos com acento
    regex: str = r"^[A-Za-zÀ-ÖØ-öø-ÿ\s]+$"
    return bool(re.fullmatch(regex, nome_limpo))


# =================================================================
# 3. SEGURANÇA E CREDENCIAIS
# =================================================================

@validar
def validar_senha(senha: str) -> Dict[str, Any]:
    """Verifica a força da senha baseando-se em requisitos de complexidade.

    Regras exigidas:
    - Mínimo de 8 caracteres
    - Não conter espaços em branco
    - Pelo menos 1 letra minúscula
    - Pelo menos 1 letra maiúscula
    - Pelo menos 1 número e 1 caractere especial (@$!%*?&)

    Args:
        senha (str): A senha em texto puro.

    Returns:
        Dict[str, Any]: Dicionário contendo 'condicao' (bool) e 'mensagem' (str).
    """
    minimo: bool = len(senha) >= 8 and " " not in senha
    minusculo: bool = bool(re.search(r"[a-z]", senha))
    maiusculo: bool = bool(re.search(r"[A-Z]", senha))
    # Verifica a presença conjunta de dígitos e caracteres especiais permitidos
    caracter_especial: bool = bool(re.search(r"\d", senha)) and bool(re.search(r"[@$!%*?&]", senha))

    all_ok: bool = minimo and minusculo and maiusculo and caracter_especial

    return {
        "condicao": all_ok,
        "mensagem": "" if all_ok else "Uma ou mais condições da senha não foi atendida",
    }


# =================================================================
# 4. VALIDAÇÕES DE COMUNICAÇÃO
# =================================================================

@validar
def validar_telefone_com_55(telefone: str) -> bool:
    """Valida o formato E.164 brasileiro incluindo o código de país (+55).

    Exemplo aceito: +5511999999999

    Args:
        telefone (str): Número de telefone formatado.

    Returns:
        bool: True se o formato for válido, False caso contrário.
    """
    if telefone == "":
        return False

    padrao: str = r"^\+55[1-9][0-9]9\d{8}$"
    return bool(re.fullmatch(padrao, telefone))


@validar
def validar_telefone(telefone: str) -> bool:
    """Valida telefone celular brasileiro (DDD + 9 dígitos) sem o prefixo +55.

    Args:
        telefone (str): Número de telefone celular.

    Returns:
        bool: True se for um celular brasileiro válido, False caso contrário.
    """
    if telefone == "":
        return False

    padrao: str = r"^[1-9]{2}9[0-9]{8}$"
    return bool(re.fullmatch(padrao, telefone))


@validar
def validar_email(email: str) -> bool:
    """Valida o formato sintático de um endereço de e-mail.

    Args:
        email (str): Endereço de e-mail a ser validado.

    Returns:
        bool: True se a sintaxe for válida e não vazia, False caso contrário.
    """
    regex_email: str = r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,}$"
    if not re.fullmatch(regex_email, email) or email == "":
        return False

    return True


# =================================================================
# 5. VALIDAÇÕES DE DOMÍNIO E CACHE
# =================================================================

@validar
def validar_dados_comite(id_comite: int, nome_comite: str) -> bool:
    """Busca e valida a existência e correspondência do comitê no cache de metadados.

    Varre as opções da chave 'aiesec-mais-proxima' guardadas no cache.

    Args:
        id_comite (int): O ID numérico do comitê.
        nome_comite (str): O nome do comitê em formato string.

    Returns:
        bool: True se encontrar correspondência exata de ID e nome; False caso contrário.
    """
    # Recupera a lista de metadados armazenados no cache global da aplicação
    cache_metadados = cache.store["metadados_card-ogx"]["data"]

    for item in cache_metadados:
        # Localiza o bloco de configuração do campo 'aiesec-mais-proxima'
        if item.get("external_id") == "aiesec-mais-proxima":
            # Itera sobre a lista de opções cadastradas
            for opcao in item.get("options", []):
                if opcao.get("id") == id_comite:
                    # Compara os nomes removendo espaços extras nas extremidades
                    if opcao.get("text", "").strip() == nome_comite.strip():
                        return True

    return False


@validar
def validar_dados_produto(nome: str, id_podio: int, id_expa: int) -> bool:
    """Valida a correspondência de um produto no Podio e no EXPA via cache de metadados.

    Args:
        nome (str): Nome do status/produto.
        id_podio (int): ID da opção correspondente no Podio.
        id_expa (int): ID do programa/produto no sistema EXPA (7, 8 ou 9).

    Returns:
        bool: True se todas as correspondências forem válidas; False caso contrário.
    """
    list_id_expa = [7, 8, 9]
    cache_metadados = cache.store["metadados_card-ogx"]["data"]

    for item in cache_metadados:
        # Localiza o bloco de configuração da chave 'status'
        if item.get("external_id") == "status":
            for opcao in item.get("options", []):
                if opcao.get("id") == id_podio:
                    # Verifica a igualdade do nome e a validação do id EXPA
                    if opcao.get("text", "").strip() == nome.strip():
                        if id_expa in list_id_expa:
                            return True

    return False


# =================================================================
# 6. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = [
    "validar_telefone",
    "validar_nome",
    "validar_senha",
    "validar_email",
    "validar_telefone_com_55",
    "validar_nome_com_acentos",
    "validar_dados_comite",
    "validar_dados_produto",
]