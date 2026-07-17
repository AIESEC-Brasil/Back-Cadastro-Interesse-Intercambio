import asyncio
from ..dto import LeadPreCadastro
from ..clients import Buscar
from ..config import APP_ID

def cadastrar_lead(body:LeadPreCadastro):
    buscar = Buscar(APP_ID)
    leadExiste = asyncio.run(buscar.item_completo(body.model_dump()))
    return leadExiste


__all__ = ["cadastrar_lead"]