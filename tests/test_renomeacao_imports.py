import importlib


def test_imports_em_portugues():
    controlador = importlib.import_module("app.controlador")
    modelo = importlib.import_module("app.modelo")
    esquema = importlib.import_module("app.esquema")

    assert hasattr(controlador, "Router")
    assert hasattr(modelo, "DivisaoCL")
    assert hasattr(modelo, "Universidades")
    assert hasattr(esquema, "divisao_CL_schema")
