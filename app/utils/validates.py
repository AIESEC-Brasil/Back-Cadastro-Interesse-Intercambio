"""
Validações utilitárias para entradas de usuário e dados de domínio.

Inclui validação de nome (com/sem acentos), senha, e-mail (gerado e pessoal),
telefone (+55 e nacional), foto base64, data de nascimento e tipos de campos.
"""

# ==============================
# Importações (Dependencies)
# ==============================
import base64  # Para decodificação e validação de arquivos em strings base64
from typing import Dict, Any, List  # Utilitários de sistema e tipos
from datetime import  datetime, date
import re, unicodedata

# ==============================
# Validações de Identidade
# ==============================
@validar
def validar_nome(nome: str) -> bool:
    """
    Valida se o nome contém apenas letras e espaços, após remover acentuação.

    Args:
        nome (str): String original contendo o nome do usuário.

    Returns:
        bool: True se for um nome válido (alfabético), False caso contrário.
    """
    if not nome:
        return False
    # Normaliza e remove acentos para validar apenas os caracteres base
    nome_sem_acentos: str = ''.join(c for c in unicodedata.normalize('NFD', nome) if unicodedata.category(c) != 'Mn')

    # Busca por qualquer caractere que NÃO seja letra ou espaço
    if re.search(r'[^A-Za-z\s]', nome_sem_acentos):
        return False

    # Garante que não restou apenas uma string vazia após a limpeza
    nome_limpo: str = re.sub(r'\s+', ' ', nome_sem_acentos).strip()
    return bool(nome_limpo)

@validar
def validar_nome_com_acentos(nome: str) -> bool:
    """
    Valida nomes permitindo caracteres acentuados latinos.

    Args:
        nome (str): Nome a ser validado.

    Returns:
        bool: True se o nome contiver apenas letras (acentuadas ou não) e espaços.
    """
    if not nome:
        return False
    nome_limpo: str = ' '.join(nome.strip().split())
    # Regex cobre o intervalo de caracteres acentuados da tabela Unicode/Latin-1
    regex: str = r'^[A-Za-zÀ-ÖØ-öø-ÿ\s]+$'
    return bool(re.fullmatch(regex, nome_limpo))

# ==============================
# Segurança e Credenciais
# ==============================
@validar
def validar_senha(senha: str) -> Dict[str, Any]:
    """
    Verifica a força da senha baseada em requisitos de complexidade.

    Regras: Mínimo 8 caracteres, sem espaços, 1 maiúscula, 1 minúscula, 1 número e 1 especial.



    Args:
        senha (str): A senha em texto puro.

    Returns:
        Dict[str, Any]: Dicionário com 'condicao' (bool) e 'mensagem' (str).
    """
    minimo: bool = len(senha) >= 8 and ' ' not in senha
    minusculo: bool = bool(re.search(r'[a-z]', senha))
    maiusculo: bool = bool(re.search(r'[A-Z]', senha))
    # Verifica simultaneamente número e caractere especial definido
    caracter_especial: bool = bool(re.search(r'\d', senha)) and bool(re.search(r'[@$!%*?&]', senha))

    all_ok: bool = minimo and minusculo and maiusculo and caracter_especial
    return {
        "condicao": all_ok,
        "mensagem": "" if all_ok else "Uma ou mais condições da senha não foi atendida"
    }

# ==============================
# Validações de Comunicação
# ==============================
@validar
def validar_telefone_com_55(telefone: str) -> bool:
    """
    Valida o formato E.164 brasileiro com o prefixo do país (+55).
    Exemplo: +5511999999999
    """
    if telefone == "":
        return True
    padrao: str = r'^\+55[1-9][0-9]9\d{8}$'
    return bool(re.fullmatch(padrao, telefone))

@validar
def validar_telefone(telefone: str) -> bool:
    """Valida telefone celular brasileiro (DDD + 9 dígitos) sem o prefixo do país."""
    padrao: str = r'^[1-9][0-9]9\d{8}$'
    return bool(re.fullmatch(padrao, telefone))

@validar
def validar_email(email: str) -> bool:
    """
    Valida se o e-mail pessoal pertence a domínios de grandes provedores.

    Args:
        email (str): E-mail pessoal fornecido.

    Returns:
        bool: True se vazio ou pertencente a: gmail, hotmail, outlook ou yahoo.
    """
    dominios_permitidos: List[str] = ['gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com']
    if email == "":
        return True

    regex_email: str = r'^[\w\.-]+@([\w-]+\.)+[\w-]{2,4}$'
    if not re.fullmatch(regex_email, email):
        return False

    dominio: str = email.split('@')[1].lower()
    return dominio in dominios_permitidos

# ==============================
# Exportações
# ==============================
__all__ = [
    "validar_telefone",
    "validar_nome",
    "validar_senha",
    "validar_email",
    "validar_telefone_com_55",
    "validar_nome_com_acentos"
]