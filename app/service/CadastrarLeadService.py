import asyncio
from typing import Any,List
from flask import jsonify, Response
from ..dto import CriarPreCadastroLead,HttpStatus
from ..clients import Buscar
from ..config import APP_ID

@validar
def cadastrar_lead(lead_input:CriarPreCadastroLead) -> tuple[dict[str, str], int] | tuple[Response, HttpStatus] | tuple[
    dict[str, Any], int]:
    BUSCAR = Buscar(APP_ID)
    leadExiste = asyncio.run(BUSCAR.item_completo(lead_input.model_dump()))
    if leadExiste:
        return {"exist":""},200
    # Verificando se já não existe cadastro com o e-mails ou emails
    CONFLITO_EMAIL = []
    CONFLITO_TELEFONE = []
    LISTA_EMAILS:List = [e.email for e in lead_input.email] # separa os e-mails informados
    for email in LISTA_EMAILS:
        qtd_emails_encontrados = asyncio.run(BUSCAR.campo("email",email,True)) # busca no podio o e-mail
        if len(qtd_emails_encontrados) > 0 : # se existir um registroo gera um conflito
            CONFLITO_EMAIL.append({"email":email})

    LISTA_TELEFONE = [t.numero for t in lead_input.telefone]
    for telefone in LISTA_TELEFONE:
        qtd_telefones_encontrados = asyncio.run(BUSCAR.telefone(telefone))
        if len(qtd_telefones_encontrados) > 0:
            CONFLITO_TELEFONE.append({"numero":telefone})

    if len(CONFLITO_EMAIL) > 0 or len(CONFLITO_TELEFONE) > 0:
        CONFLITOS = []

        if len(CONFLITO_EMAIL) > 0:
            CONFLITOS.append({"emails":CONFLITO_EMAIL})

        if len(CONFLITO_TELEFONE) > 0:
            CONFLITOS.append({"telefone":CONFLITO_TELEFONE})

        return jsonify({"conflito":CONFLITOS}),HttpStatus.CONFLICT

    return {"sucess":lead_input.model_dump()},201


__all__ = ["cadastrar_lead"]