"""API de consulta de auditoría: GET /auditoria?turno_id= (C-15, US-014, Flujo 7)."""

import re

from tests.api.test_turnos import (  # noqa: F401  (contexto_turnos es una fixture)
    CLAVES_SNAPSHOT,
    LUNES,
    ContextoTurnos,
    _cantidad,
    contexto_turnos,
)

FORMATO_OCURRIO_EN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")


def _reservar(ctx: ContextoTurnos) -> int:
    respuesta = ctx.reservar(ctx.cuerpo(f"{LUNES}T10:00:00"), ctx.cabeceras_admin)
    assert respuesta.status_code == 201
    return int(respuesta.json()["id"])


def _reprogramar(ctx: ContextoTurnos, turno_id: int) -> None:
    respuesta = ctx.cliente.post(
        f"/turnos/{turno_id}/reprogramar",
        json={"nuevo_inicio": f"{LUNES}T11:00:00"},
        headers=ctx.cabeceras_admin,
    )
    assert respuesta.status_code == 200


def _cancelar(ctx: ContextoTurnos, turno_id: int) -> None:
    respuesta = ctx.cliente.post(f"/turnos/{turno_id}/cancelar", headers=ctx.cabeceras_admin)
    assert respuesta.status_code == 200


def _historial_completo(ctx: ContextoTurnos) -> int:
    """Crea, reprograma y cancela un turno; devuelve su id."""
    turno_id = _reservar(ctx)
    _reprogramar(ctx, turno_id)
    _cancelar(ctx, turno_id)
    return turno_id


def _consultar(ctx: ContextoTurnos, turno_id: int):  # type: ignore[no-untyped-def]
    return ctx.cliente.get(
        f"/auditoria?turno_id={turno_id}", headers=ctx.cabeceras_admin
    )


# --- 2.1 contrato de la respuesta ---


def test_historial_de_tres_acciones_devuelve_tres_registros_en_orden(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    turno_id = _historial_completo(ctx)

    respuesta = _consultar(ctx, turno_id)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["turno_id"] == turno_id
    assert [registro["accion"] for registro in cuerpo["registros"]] == [
        "crear",
        "reprogramar",
        "cancelar",
    ]


def test_turno_recien_creado_devuelve_solo_el_alta(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    turno_id = _reservar(ctx)

    respuesta = _consultar(ctx, turno_id)

    assert respuesta.status_code == 200
    registros = respuesta.json()["registros"]
    assert len(registros) == 1
    assert registros[0]["accion"] == "crear"


def test_antes_y_despues_son_objetos_con_las_ocho_claves(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    turno_id = _historial_completo(ctx)

    registros = _consultar(ctx, turno_id).json()["registros"]

    for registro in registros:
        assert isinstance(registro["despues"], dict)
        assert list(registro["despues"]) == CLAVES_SNAPSHOT
        if registro["antes"] is not None:
            assert isinstance(registro["antes"], dict)
            assert list(registro["antes"]) == CLAVES_SNAPSHOT


def test_antes_es_nulo_solo_en_el_alta(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    turno_id = _historial_completo(ctx)

    registros = _consultar(ctx, turno_id).json()["registros"]

    assert registros[0]["antes"] is None
    assert registros[1]["antes"] is not None
    assert registros[2]["antes"] is not None


def test_reprogramacion_conserva_el_id_y_cambia_el_inicio(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    turno_id = _historial_completo(ctx)

    reprogramar = _consultar(ctx, turno_id).json()["registros"][1]

    assert reprogramar["antes"]["id"] == turno_id
    assert reprogramar["despues"]["id"] == turno_id
    assert reprogramar["antes"]["inicio"] == f"{LUNES}T10:00:00"
    assert reprogramar["despues"]["inicio"] == f"{LUNES}T11:00:00"


def test_ocurrio_en_tiene_formato_iso_de_segundos(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    turno_id = _historial_completo(ctx)

    registros = _consultar(ctx, turno_id).json()["registros"]

    for registro in registros:
        assert FORMATO_OCURRIO_EN.match(registro["ocurrio_en"])


# --- 2.3 turno_id obligatorio y existencia ---


def test_turno_id_ausente_422(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos

    respuesta = ctx.cliente.get("/auditoria", headers=ctx.cabeceras_admin)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"


def test_turno_id_cero_422(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos

    respuesta = ctx.cliente.get("/auditoria?turno_id=0", headers=ctx.cabeceras_admin)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"


def test_turno_id_negativo_422(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos

    respuesta = ctx.cliente.get("/auditoria?turno_id=-1", headers=ctx.cabeceras_admin)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"


def test_turno_id_no_entero_422(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos

    respuesta = ctx.cliente.get("/auditoria?turno_id=abc", headers=ctx.cabeceras_admin)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"


def test_turno_inexistente_404_no_encontrado(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos

    respuesta = ctx.cliente.get("/auditoria?turno_id=999999", headers=ctx.cabeceras_admin)

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "no_encontrado"


# --- 2.4 identidad y datos sensibles ---


def test_username_identifica_al_usuario_que_opero(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    turno_id = _reservar(ctx)

    registros = _consultar(ctx, turno_id).json()["registros"]

    assert registros[0]["usuario_id"] == ctx.admin.id
    assert registros[0]["username"] == "admin_ficticio"


def test_usuario_desactivado_sigue_apareciendo(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    respuesta = ctx.reservar(ctx.cuerpo(f"{LUNES}T10:00:00"), ctx.cabeceras_recepcion)
    assert respuesta.status_code == 201
    turno_id = int(respuesta.json()["id"])

    baja = ctx.cliente.patch(
        f"/usuarios/{ctx.recepcion.id}", json={"activo": False}, headers=ctx.cabeceras_admin
    )
    assert baja.status_code == 200

    registros = _consultar(ctx, turno_id).json()["registros"]

    assert registros[0]["usuario_id"] == ctx.recepcion.id
    assert registros[0]["username"] == "recepcion_ficticia"


def _claves(objeto: object) -> set[str]:
    """Todas las claves de un JSON anidado."""
    if isinstance(objeto, dict):
        claves = set(objeto)
        for valor in objeto.values():
            claves |= _claves(valor)
        return claves
    if isinstance(objeto, list):
        claves: set[str] = set()
        for item in objeto:
            claves |= _claves(item)
        return claves
    return set()


def test_respuesta_sin_datos_sensibles(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    turno_id = _historial_completo(ctx)

    cuerpo = _consultar(ctx, turno_id).json()
    claves = _claves(cuerpo)

    assert claves.isdisjoint({"password_hash", "password", "rol", "dni", "nombre", "apellido"})
    assert "usuario_id" in claves
    assert "username" in claves


# --- 3.1 acceso restringido ---


def test_sin_token_401_no_autenticado(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    turno_id = _reservar(ctx)

    respuesta = ctx.cliente.get(f"/auditoria?turno_id={turno_id}")

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"


def test_recepcion_403_sin_permiso(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    turno_id = _reservar(ctx)

    respuesta = ctx.cliente.get(
        f"/auditoria?turno_id={turno_id}", headers=ctx.cabeceras_recepcion
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"


def test_odontologo_403_sin_permiso(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    turno_id = _reservar(ctx)

    respuesta = ctx.cliente.get(
        f"/auditoria?turno_id={turno_id}", headers=ctx.cabeceras_odontologo_a
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"


def test_rol_sin_permiso_con_turno_inexistente_recibe_403_no_404(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos

    respuesta = ctx.cliente.get("/auditoria?turno_id=999999", headers=ctx.cabeceras_recepcion)

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"


# --- 3.2 solo lectura (RN-AUD-02) ---


def test_patch_y_delete_sobre_auditoria_405_sin_cambios(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    turno_id = _reservar(ctx)
    antes = _cantidad(ctx, "auditoria")

    patch = ctx.cliente.patch("/auditoria", headers=ctx.cabeceras_admin)
    delete = ctx.cliente.delete("/auditoria", headers=ctx.cabeceras_admin)

    assert patch.status_code == 405
    assert patch.json()["codigo"] == "metodo_no_permitido"
    assert delete.status_code == 405
    assert delete.json()["codigo"] == "metodo_no_permitido"
    assert _cantidad(ctx, "auditoria") == antes


def test_patch_y_delete_sobre_auditoria_id_404_sin_cambios(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    turno_id = _reservar(ctx)
    antes = _cantidad(ctx, "auditoria")

    patch = ctx.cliente.patch(f"/auditoria/{turno_id}", headers=ctx.cabeceras_admin)
    delete = ctx.cliente.delete(f"/auditoria/{turno_id}", headers=ctx.cabeceras_admin)

    assert patch.status_code == 404
    assert patch.json()["codigo"] == "no_encontrado"
    assert delete.status_code == 404
    assert delete.json()["codigo"] == "no_encontrado"
    assert _cantidad(ctx, "auditoria") == antes
