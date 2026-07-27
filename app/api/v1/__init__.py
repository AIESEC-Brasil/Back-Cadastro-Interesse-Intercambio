from .paginacao import escritorios,universidades
from app.router import Router

v1 = Router(name="v1",url_prefix="/v1")

v1.register_api(escritorios)
v1.register_api(universidades)

__all__ = ["v1"]
