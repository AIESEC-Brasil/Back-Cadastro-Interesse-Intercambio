"""
Utilitários de data e hora com suporte a fuso horário do Brasil (America/Sao_Paulo).

Este módulo centraliza funções para obter o horário atual com e sem timezone,
formatar datas em padrões brasileiros, calcular expiração e converter timestamps
para o formato esperado pelo sistema de logging.
"""

# ==============================
# Importações (Dependencies)
# ==============================
import pytz  # Biblioteca para manipulação de definições de fuso horário (IANA database)
import locale  # Permite a localização de strings (como nomes de meses em português)
import time  # Fornece o tipo struct_time para o logging
from datetime import timedelta  # Utilizado para cálculos de aritmética de datas
from zoneinfo import ZoneInfo
from datetime import datetime  # Instância global de datetime para consistência no projeto



# ==============================
# Funções de Tempo Atual
# ==============================
@validar
def agora_timestamp(cidade_fuso: str = "America/Sao_Paulo") -> float:
    """
    Retorna o timestamp atual (Unix Epoch) no fuso informado.

    Args:
        cidade_fuso (str): Identificador do fuso horário IANA.

    Returns:
        float: Segundos decorridos desde 01/01/1970 (Epoch).
    """
    SEGUNDOS_HORAS:int = 3600 # constante refletindo 1 hora em segundos
    fuso = pytz.timezone(str(cidade_fuso))
    time_zone:float = float(ZoneInfo(cidade_fuso).tzname(datetime.now(fuso))) * SEGUNDOS_HORAS
    return datetime.now(fuso).timestamp() + time_zone

@validar
def agora(cidade_fuso: str = "America/Sao_Paulo") -> datetime:
    """
    Retorna o objeto datetime atual com informação de fuso horário (aware).

    Args:
        cidade_fuso (str): Identificador do fuso horário IANA.

    Returns:
        datetime: Objeto datetime localizado no fuso especificado.
    """
    fuso = pytz.timezone(str(cidade_fuso))
    return datetime.now(fuso)

@validar
def agora_sem_timezone(cidade_fuso: str = "America/Sao_Paulo") -> datetime:
    """
    Retorna o datetime atual no fuso informado, mas remove o objeto tzinfo (naive).
    Ideal para salvar em bancos de dados que não gerenciam timezones nativamente.

    Args:
        cidade_fuso (str): Identificador do fuso horário IANA.

    Returns:
        datetime: Objeto datetime sem informação de fuso (naive).
    """
    fuso = pytz.timezone(str(cidade_fuso))
    return datetime.now(fuso).replace(tzinfo=None)

# ==============================
# Cálculos e Formatações
# ==============================

@validar
def agora_format_brasil(cidade_fuso: str = "America/Sao_Paulo") -> str:
    """
    Retorna string formatada no padrão brasileiro curto.

    Args:
        cidade_fuso (str): Identificador do fuso horário IANA.

    Returns:
        str: Data e hora no formato 'DD/MM/AAAA HH:MM:SS'.
    """
    return agora(cidade_fuso).strftime("%d/%m/%Y %H:%M:%S")

@validar
def agora_format_brasil_mes(cidade_fuso: str = "America/Sao_Paulo") -> str:
    """
    Retorna data formatada com mês abreviado em português.

    Args:
        cidade_fuso (str): Identificador do fuso horário IANA.

    Returns:
        str: Data e hora formatada (ex: '14/Fev/2026 21:45:00').
    """
    return agora(cidade_fuso).strftime(f"%d/%b/%Y %H:%M:%S").title()

# ==============================
# Integração com Logging
# ==============================
@validar
def logging_time_brasil(*args) -> time.struct_time:
    """
    Hook de conversão de tempo para o Formatador do Logging do Python.



    Args:
        *args: Argumentos variáveis passados pelo logging (o último é o timestamp).

    Returns:
        time.struct_time: Objeto de tempo compatível com a biblioteca padrão de logging.
    """
    # O logging costuma passar o timestamp como último argumento da tupla
    seconds = args[-1]

    cidade_fuso = "America/Sao_Paulo"
    tz = pytz.timezone(cidade_fuso)

    # Fallback caso o timestamp recebido seja inválido
    if not isinstance(seconds, (int, float)):
        seconds = datetime.now().timestamp()

    # Localiza o timestamp para o fuso de Brasília antes de converter para struct_time
    dt = datetime.fromtimestamp(seconds, tz)
    return dt.timetuple()

# ==============================
# Exportações
# ==============================
__all__ = [
    "agora_timestamp",
    "agora",
    "agora_format_brasil",
    "logging_time_brasil",
    "agora_format_brasil_mes",
    "agora_sem_timezone"
]