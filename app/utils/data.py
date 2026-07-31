"""Utilitários de data e hora com suporte a fuso horário do Brasil (America/Sao_Paulo).

Este módulo centraliza funções para obter o horário atual com e sem timezone,
formatar datas em padrões brasileiros, calcular expiração e converter timestamps
para o formato esperado pelo sistema de logging nativo do Python.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from datetime import datetime, timedelta  # Aritmética e manipulação de objetos datetime
import locale  # Configuração regional para formatação de meses em português
import time  # Estruturas de tempo de baixo nível (struct_time) para logging
from zoneinfo import ZoneInfo  # Suporte nativo do Python a fusos horários IANA

import pytz  # Biblioteca de fusos horários IANA estendida

# Tenta definir a localização temporal para o idioma português do Brasil
try:
    locale.setlocale(locale.LC_TIME, "pt_BR.utf-8")
except Exception:
    try:
        locale.setlocale(locale.LC_TIME, "pt_BR")
    except Exception:
        pass


# =================================================================
# 2. FUNÇÕES DE TEMPO ATUAL
# =================================================================

@validar
def agora_timestamp(cidade_fuso: str = "America/Sao_Paulo") -> float:
    """Retorna o timestamp Unix ajustado para o fuso local (-3 horas em relação a UTC).

    Args:
        cidade_fuso (str): Identificador do fuso horário IANA (ex: 'America/Sao_Paulo').

    Returns:
        float: Valor numérico em segundos ajustado para o horário local.
    """
    SEGUNDOS_POR_HORA: int = 3600
    OFFSET_HORAS: int = 3  # Subtração das 3 horas em relação a Greenwich

    fuso = pytz.timezone(str(cidade_fuso))
    dt_atual = datetime.now(fuso)

    # Aplica o desconto de 3 horas (10.800 segundos) sobre o UTC
    return dt_atual.timestamp() - (OFFSET_HORAS * SEGUNDOS_POR_HORA)


@validar
def agora(cidade_fuso: str = "America/Sao_Paulo") -> datetime:
    """Retorna o objeto datetime atual com informação de fuso horário (aware).

    Args:
        cidade_fuso (str): Identificador do fuso horário IANA.

    Returns:
        datetime: Objeto datetime ciente do fuso especificado.
    """
    fuso = pytz.timezone(str(cidade_fuso))
    return datetime.now(fuso)


@validar
def agora_sem_timezone(cidade_fuso: str = "America/Sao_Paulo") -> datetime:
    """Retorna o datetime atual no fuso informado, mas sem informação de tz (naive).

    Ideal para salvar em bancos de dados que armazenam datas sem timezone nativo.

    Args:
        cidade_fuso (str): Identificador do fuso horário IANA.

    Returns:
        datetime: Objeto datetime ingênuo (sem tzinfo).
    """
    fuso = pytz.timezone(str(cidade_fuso))
    return datetime.now(fuso).replace(tzinfo=None)


# =================================================================
# 3. CÁLCULOS E FORMATAÇÕES DE DATA/HORA
# =================================================================

@validar
def agora_format_brasil(cidade_fuso: str = "America/Sao_Paulo") -> str:
    """Retorna a data e hora formatadas no padrão brasileiro numérico.

    Args:
        cidade_fuso (str): Identificador do fuso horário IANA.

    Returns:
        str: Data formatada como 'DD/MM/AAAA HH:MM:SS'.
    """
    return agora(cidade_fuso).strftime("%d/%m/%Y %H:%M:%S")


@validar
def agora_format_brasil_mes(cidade_fuso: str = "America/Sao_Paulo") -> str:
    """Retorna a data formatada com a abreviação do mês em português.

    Args:
        cidade_fuso (str): Identificador do fuso horário IANA.

    Returns:
        str: Data formatada (ex: '14/Fev/2026 21:45:00').
    """
    return agora(cidade_fuso).strftime("%d/%b/%Y %H:%M:%S").title()


# =================================================================
# 4. INTEGRAÇÃO COM SISTEMA DE LOGGING
# =================================================================

@validar
def logging_time_brasil(*args) -> time.struct_time:
    """Hook de conversão de tempo para o Formatador do módulo de Logging do Python.

    Args:
        *args: Argumentos variados passados pelo logging (o último elemento é o timestamp).

    Returns:
        time.struct_time: Estrutura de tempo compatível com a biblioteca nativa de logging.
    """
    seconds = args[-1] if args else None

    cidade_fuso = "America/Sao_Paulo"
    tz = pytz.timezone(cidade_fuso)

    if not isinstance(seconds, (int, float)):
        seconds = datetime.now().timestamp()

    dt = datetime.fromtimestamp(seconds, tz)
    return dt.timetuple()


# =================================================================
# 5. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = [
    "agora_timestamp",
    "agora",
    "agora_format_brasil",
    "logging_time_brasil",
    "agora_format_brasil_mes",
    "agora_sem_timezone",
]