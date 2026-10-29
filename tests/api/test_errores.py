"""Tests del formato global de errores {codigo, mensaje, detalles?} (C-03, RN-GLO-01)."""

import pytest
from fastapi import APIRouter, HTTPException
from fastapi.testclient import TestClient

from app.api.errores import MAPEO_DOMINIO
from app.config import Config
from app.domain.errores import ErrorDominio
from app.main import create_app
from tests.api.rutas_prueba import (
    MENSAJE_CONFLICTO_AGENDA,
    MENSAJE_DATO_INVALIDO,
    MENSAJE_DENTRO_DE_BLOQUEO,
    MENSAJE_FUERA_DE_HORARIO,
    MENSAJE_NOMBRE_DUPLICADO,
)


@pytest.mark.parametrize(
    ("ruta", "status", "codigo", "mensaje"),
    [
        ("/prueba/error/conflicto-agenda", 409, "conflicto_agenda", MENSAJE_CONFLICTO_AGENDA),
        ("/prueba/error/fuera-de-horario", 409, "fuera_de_horario", MENSAJE_FUERA_DE_HORARIO),
        ("/prueba/error/dentro-de-bloqueo", 409, "dentro_de_bloqueo", MENSAJE_DENTRO_DE_BLOQUEO),
        ("/prueba/error/dato-invalido", 422, "dato_invalido", MENSAJE_DATO_INVALIDO),
        ("/prueba/error/nombre-duplicado", 409, "nombre_duplicado", MENSAJE_NOMBRE_DUPLICADO),
    ],
)
def test_error_de_dominio_responde_su_status_con_codigo_y_mensaje(
    cliente_con_rutas_prueba: TestClient, ruta: str, status: int, codigo: str, mensaje: str
) -> None:
    respuesta = cliente_con_rutas_prueba.get(ruta)

    assert respuesta.status_code == status
    assert respuesta.json() == {"codigo": codigo, "mensaje": mensaje}


def test_ruta_inexistente_responde_404_no_encontrado(cliente: TestClient) -> None:
    respuesta = cliente.get("/no-existe")

    assert respuesta.status_code == 404
    cuerpo = respuesta.json()
    assert cuerpo.keys() == {"codigo", "mensaje"}
    assert cuerpo["codigo"] == "no_encontrado"
    assert cuerpo["mensaje"]


def test_metodo_no_admitido_responde_405_metodo_no_permitido(
    cliente_con_rutas_prueba: TestClient,
) -> None:
    respuesta = cliente_con_rutas_prueba.post("/prueba/error/conflicto-agenda")

    assert respuesta.status_code == 405
    cuerpo = respuesta.json()
    assert cuerpo.keys() == {"codigo", "mensaje"}
    assert cuerpo["codigo"] == "metodo_no_permitido"
    assert cuerpo["mensaje"]
    assert respuesta.headers["allow"] == "GET"


def test_docs_fuera_de_development_responde_el_404_propio(cliente: TestClient) -> None:
    respuesta = cliente.get("/docs")

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "no_encontrado"


def test_otro_error_http_conserva_su_status_con_codigo_error_http(config: Config) -> None:
    router = APIRouter()

    @router.get("/prueba/error/http-400")
    def lanzar_http_400() -> None:
        raise HTTPException(status_code=400, detail="Detalle en inglés que no debe salir.")

    aplicacion = create_app(config)
    aplicacion.include_router(router)

    with TestClient(aplicacion) as cliente_http:
        respuesta = cliente_http.get("/prueba/error/http-400")

    assert respuesta.status_code == 400
    cuerpo = respuesta.json()
    assert cuerpo.keys() == {"codigo", "mensaje"}
    assert cuerpo["codigo"] == "error_http"
    assert cuerpo["mensaje"] != "Detalle en inglés que no debe salir."


def test_body_vacio_responde_422_con_un_detalle_por_campo_faltante(
    cliente_con_rutas_prueba: TestClient,
) -> None:
    respuesta = cliente_con_rutas_prueba.post("/prueba/validacion", json={})

    assert respuesta.status_code == 422
    assert respuesta.json() == {
        "codigo": "dato_invalido",
        "mensaje": "Los datos enviados no son válidos.",
        "detalles": [
            {"campo": "username", "mensaje": "Campo obligatorio."},
            {"campo": "password", "mensaje": "Campo obligatorio."},
        ],
    }


def test_tipo_incorrecto_responde_422_con_el_campo_sin_prefijo_body(
    cliente_con_rutas_prueba: TestClient,
) -> None:
    respuesta = cliente_con_rutas_prueba.post(
        "/prueba/validacion", json={"username": "recepcion_ficticia", "password": 123}
    )

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "dato_invalido"
    assert cuerpo["detalles"] == [{"campo": "password", "mensaje": "Debe ser un texto."}]


def test_json_mal_formado_responde_422_dato_invalido(
    cliente_con_rutas_prueba: TestClient,
) -> None:
    respuesta = cliente_con_rutas_prueba.post(
        "/prueba/validacion",
        content=b'{"username": ',
        headers={"Content-Type": "application/json"},
    )

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "dato_invalido"
    # El loc de Pydantic trae la posición del carácter; el campo es todo el cuerpo.
    assert cuerpo["detalles"] == [
        {"campo": "body", "mensaje": "El cuerpo no es un JSON válido."}
    ]


def test_body_que_no_es_un_objeto_usa_campo_body_y_valor_invalido(
    cliente_con_rutas_prueba: TestClient,
) -> None:
    respuesta = cliente_con_rutas_prueba.post("/prueba/validacion", json=["no-es-un-objeto"])

    assert respuesta.status_code == 422
    assert respuesta.json()["detalles"] == [{"campo": "body", "mensaje": "Valor inválido."}]


@pytest.mark.parametrize(
    ("ruta", "codigo", "mensaje"),
    [
        (
            "/prueba/error/no-autenticado",
            "no_autenticado",
            "Se requiere un token de acceso válido.",
        ),
        (
            "/prueba/error/credenciales-invalidas",
            "credenciales_invalidas",
            "Usuario o contraseña incorrectos.",
        ),
    ],
)
def test_errores_de_autenticacion_responden_401_con_www_authenticate(
    cliente_con_rutas_prueba: TestClient, ruta: str, codigo: str, mensaje: str
) -> None:
    respuesta = cliente_con_rutas_prueba.get(ruta)

    assert respuesta.status_code == 401
    assert respuesta.headers["www-authenticate"] == "Bearer"
    assert respuesta.json() == {"codigo": codigo, "mensaje": mensaje}


def test_sin_permiso_responde_403_sin_www_authenticate(
    cliente_con_rutas_prueba: TestClient,
) -> None:
    respuesta = cliente_con_rutas_prueba.get("/prueba/error/sin-permiso")

    assert respuesta.status_code == 403
    assert "www-authenticate" not in respuesta.headers
    assert respuesta.json() == {
        "codigo": "sin_permiso",
        "mensaje": "Tu rol no tiene permiso para esta operación.",
    }


class ErrorDominioSinMapeo(ErrorDominio):
    """Error de dominio definido solo en el test, sin entrada en la tabla de mapeo."""


def _subclases(clase: type[ErrorDominio]) -> set[type[ErrorDominio]]:
    """Todas las subclases de `clase`, a cualquier profundidad."""
    directas = set(clase.__subclasses__())
    return directas.union(*(_subclases(subclase) for subclase in directas))


def test_todo_error_de_dominio_de_la_app_tiene_entrada_en_el_mapeo() -> None:
    # Se excluyen las subclases definidas en los tests (como ErrorDominioSinMapeo).
    subclases_de_la_app = {
        subclase for subclase in _subclases(ErrorDominio) if subclase.__module__.startswith("app.")
    }

    assert subclases_de_la_app
    assert subclases_de_la_app - MAPEO_DOMINIO.keys() == set()


def test_error_de_dominio_sin_mapeo_responde_500_error_interno(config: Config) -> None:
    router = APIRouter()

    @router.get("/prueba/error/sin-mapeo")
    def lanzar_error_sin_mapeo() -> None:
        raise ErrorDominioSinMapeo("Detalle interno que no debe filtrarse (ficticio).")

    aplicacion = create_app(config)
    aplicacion.include_router(router)

    with TestClient(aplicacion) as cliente_http:
        respuesta = cliente_http.get("/prueba/error/sin-mapeo")

    assert respuesta.status_code == 500
    assert respuesta.json() == {"codigo": "error_interno", "mensaje": "Error interno."}
