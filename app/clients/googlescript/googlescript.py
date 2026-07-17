"""
Cliente para integração com Google Apps Script (envio de e-mails PSEL).

Utiliza um HttpClient com base na URL pública do Apps Script, compondo o path
com o ID do script e o endpoint /exec.
"""

# ==============================
# Importações (Dependencies)
# ==============================
from app.clients.http_request import HttpClient          # Cliente base para chamadas externas
from app.config import ID_APPSCRIPT_EMAIL_LEADS_PSEL    # ID único do script (Deploy ID)
from app.utils import resolve_response                  # Trata a natureza assíncrona da resposta

# =================================================================
# INSTÂNCIA DE CLIENTE (Contexto Google Macros)
# =================================================================

#

# Define a base_url para os servidores de macro do Google.
# O prefixo '/macros/s' é o padrão para scripts publicados como Web Apps.
http = HttpClient(base_url="https://script.google.com", prefix="/macros/s")

# =================================================================
# FUNÇÕES DE NEGÓCIO
# =================================================================

@validar
def enviar_email_psel(payload: dict) -> None:
    """
    Dispara a execução do Apps Script responsável por enviar e-mails do PSEL.

    Lógica:
    - O Apps Script, ao receber um POST no endpoint /exec, aciona a função 'doPost(e)'.
    - O payload contém informações como destinatário, assunto e corpo (ou templates).

    Args:
        payload: Dicionário contendo os dados parametrizados para o e-mail.
    """

    #

    # Constrói o caminho final: /macros/s/{SCRIPT_ID}/exec
    # Utilizamos o resolve_response para garantir que a requisição POST seja
    # enviada e aguardada corretamente antes de finalizar a função.
    resolve_response(
        http.post(
            path=f"/{ID_APPSCRIPT_EMAIL_LEADS_PSEL}/exec",
            payload=payload
        )
    )

# ==============================
# Exportações do Módulo
# ==============================
__all__ = [
    ""
]