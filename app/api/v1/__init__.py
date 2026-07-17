from .paginacao import escritorios
from app.controller import Router

v1 = Router(name="v1",url_prefix="/v1")

v1.register_api(escritorios)

__all__ = ["v1"]
