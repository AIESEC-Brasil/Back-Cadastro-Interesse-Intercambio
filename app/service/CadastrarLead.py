import asyncio
from ..dto import LeadPreCadastro
from ..clients import Buscar
from ..config import APP_ID

@validar
def cadastrar_lead(body:LeadPreCadastro):
    buscar = Buscar(APP_ID)
    leadExiste = asyncio.run(buscar.item_completo(body.model_dump()))
    if leadExiste:
        return
    return "sucess",201


__all__ = ["cadastrar_lead"]