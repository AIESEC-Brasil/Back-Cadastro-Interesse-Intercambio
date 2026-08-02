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
from app.dto import AppError,BaseErrorResponse,HttpStatus # DTO para resposta de erro
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
def validar_senha(senha: str) -> str:
    """Verifica a força da senha baseando-se em requisitos de complexidade e caracteres permitidos.

    Avalia a string enviada contra um conjunto de regras de segurança para garantir
    a robustez da credencial e evitar falhas de parsing ou injeções de código. Acumula
    todas as falhas encontradas dentro do modelo estruturado 'BaseErrorResponse'
    e as dispara em um 'ValueError'.

    Regras exigidas:
    - Mínimo de 8 caracteres
    - Não conter espaços em branco
    - Não conter caracteres proibidos (; ' " ` \\ tabulação/quebras de linha) ou de controle
    - Pelo menos 1 letra minúscula
    - Pelo menos 1 letra maiúscula
    - Pelo menos 1 número
    - Pelo menos 1 caractere especial permitido (@$!%*?&)

    Args:
        senha (str): A string contendo a senha em texto puro a ser validada.

    Returns:
        str: A própria senha enviada, sem alterações, caso atenda a todos os requisitos.

    Raises:
        ValueError: Se a senha violar uma ou mais regras de segurança. O argumento
                    da exceção conterá a instância do DTO BaseErrorResponse.
    """
    # Define o conjunto de caracteres proibidos por motivos de parsing e segurança (SQLi, XSS, Command Injection)
    caracteres_proibidos = {";", "'", '"', "`", "\\", "\t", "\n", "\r"}

    # Lista que acumulará os dicionários no formato exigido pela propriedade 'error_details' do DTO
    error_details: list[str] = []

    # =================================================================
    # 1. AVALIAÇÃO PRÉVIA DAS CONDIÇÕES BÁSICAS DE SEGURANÇA
    # =================================================================
    # Avalia booleanamente cada critério de complexidade para a checagem global inicial
    tem_minimo: bool = len(senha) >= 8 and " " not in senha
    tem_minuscula: bool = bool(re.search(r"[a-z]", senha))
    tem_maiuscula: bool = bool(re.search(r"[A-Z]", senha))
    tem_numero: bool = bool(re.search(r"\d", senha))
    tem_especial: bool = bool(re.search(r"[@$!%*?&]", senha))

    # Trava global: Interrompe imediatamente se a entrada falhar simultaneamente em TODAS as regras
    if not any([tem_minimo, tem_minuscula, tem_maiuscula, tem_numero, tem_especial]):
        raise ValueError("Dados Inválidos: A senha enviada não atende a nenhuma das condições de segurança exigidas.")

    # =================================================================
    # 2. CHECAGEM DE CARACTERES PROIBIDOS E DE CONTROLE
    # =================================================================
    # Varre a string avaliando o código ASCII (ord) de cada caractere.
    # Caracteres com valor abaixo de 32 são considerados invisíveis ou de controle (ex: \0, \n, \t).
    if any(ord(char) < 32 for char in senha):
        error_details.append("Dados Inválidos: A senha contém caracteres invisíveis ou de controle não permitidos.")

    # Converte a senha para um 'set' (conjunto único) e realiza a intersecção matemática
    # com o conjunto de caracteres_proibidos para identificar invasões de caracteres indesejados.
    proibidos_encontrados = caracteres_proibidos.intersection(set(senha))
    if proibidos_encontrados:
        # Formata os caracteres encontrados entre aspas simples para clareza na resposta ao usuário
        fmt_proibidos = ", ".join(f"'{c}'" for c in proibidos_encontrados)
        error_details.append(f"Dados Inválidos: A senha contém caracteres não permitidos: {fmt_proibidos}.")

    # =================================================================
    # 3. TRAVAS INDIVIDUAIS DE REQUISITOS DE COMPLEXIDADE
    # =================================================================
    # Verifica o comprimento mínimo da senha
    if len(senha) < 8:
        error_details.append("Dados Inválidos: A senha deve conter no mínimo 8 caracteres.")

    # Garante a ausência de espaços em branco (espaços normais ' ')
    if " " in senha:
        error_details.append("Dados Inválidos: A senha não pode conter espaços em branco.")

    # Exige a presença de pelo menos um caractere alfabético minúsculo
    if not tem_minuscula:
        error_details.append("Dados Inválidos: A senha deve conter pelo menos uma letra minúscula.")

    # Exige a presença de pelo menos um caractere alfabético maiúsculo
    if not tem_maiuscula:
        error_details.append("Dados Inválidos: A senha deve conter pelo menos uma letra maiúscula.")

    # Exige a presença de pelo menos um caractere numérico (0-9)
    if not tem_numero:
        error_details.append("Dados Inválidos: A senha deve conter pelo menos um número.")

    # Exige a presença de pelo menos um caractere especial do conjunto permitido
    if not tem_especial:
        error_details.append("Dados Inválidos: A senha deve conter pelo menos um caractere especial (@$!%*?&).")

    # =================================================================
    # 4. DISPARO DAS FALHAS E RETORNO
    # =================================================================
    # Se a lista contiver qualquer pendência acumulada, encapsula no BaseErrorResponse e dispara no ValueError
    if len(error_details) > 0:
        raise ValueError(error_details)

    # Retorna a string pura tratada para consolidação no esquema final do Pydantic / DTO
    return senha

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