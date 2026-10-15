import importlib


def test_paquete_dominio_es_importable() -> None:
    modulo = importlib.import_module("app.domain")
    assert modulo.__name__ == "app.domain"
