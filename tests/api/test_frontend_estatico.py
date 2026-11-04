"""Tests de entrega del frontend estático y preservación del 404 JSON (C-18, RN-GLO-01)."""

from fastapi.testclient import TestClient


def test_get_raiz_responde_200_html_con_los_cuatro_contenedores_de_vista(
    cliente: TestClient,
) -> None:
    respuesta = cliente.get("/")

    assert respuesta.status_code == 200
    assert "text/html" in respuesta.headers["content-type"]
    for contenedor in ('id="login"', 'id="agenda"', 'id="crear-turno"', 'id="crear-bloqueo"'):
        assert contenedor in respuesta.text
    assert "/" not in cliente.app.openapi()["paths"]


def test_get_static_styles_css_responde_200_con_hoja_de_estilos(cliente: TestClient) -> None:
    respuesta = cliente.get("/static/styles.css")

    assert respuesta.status_code == 200
    assert "text/css" in respuesta.headers["content-type"]
    assert respuesta.text.strip()


def test_get_static_app_js_responde_200_con_javascript_compilado(cliente: TestClient) -> None:
    respuesta = cliente.get("/static/app.js")

    assert respuesta.status_code == 200
    assert "javascript" in respuesta.headers["content-type"]
    assert respuesta.text.strip()


def test_get_ruta_inexistente_conserva_404_json_en_espanol(cliente: TestClient) -> None:
    respuesta = cliente.get("/ruta-que-no-existe")

    assert respuesta.status_code == 404
    assert "application/json" in respuesta.headers["content-type"]
    assert respuesta.json() == {
        "codigo": "no_encontrado",
        "mensaje": "El recurso solicitado no existe.",
    }
