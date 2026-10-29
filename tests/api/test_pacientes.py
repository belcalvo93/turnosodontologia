"""Tests de API para pacientes y permisos RBAC (C-06, US-011, RN-PAC-01, RN-PAC-02, RN-PAC-03)."""

from collections.abc import Callable

from fastapi.testclient import TestClient

from app.domain.usuarios import Rol, Usuario


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _crear_paciente(
    cliente: TestClient,
    cabeceras: dict[str, str],
    *,
    nombre: str = "Ana",
    apellido: str = "Pérez",
    dni: str = "30111222 (ficticio)",
    telefono: str | None = None,
    obra_social: str | None = None,
    nro_afiliado: str | None = None,
) -> dict[str, object]:
    cuerpo: dict[str, object] = {
        "nombre": nombre,
        "apellido": apellido,
        "dni": dni,
    }
    if telefono is not None:
        cuerpo["telefono"] = telefono
    if obra_social is not None:
        cuerpo["obra_social"] = obra_social
    if nro_afiliado is not None:
        cuerpo["nro_afiliado"] = nro_afiliado
    return cliente.post("/pacientes", json=cuerpo, headers=cabeceras).json()


def test_post_pacientes_alta_valida_con_obra_social(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)

    respuesta = cliente.post(
        "/pacientes",
        json={
            "nombre": "  Ana  ",
            "apellido": "  Pérez  ",
            "dni": "  30111222 (ficticio)  ",
            "telefono": "  3884000001  ",
            "obra_social": "  Obra Social Norte (ficticia)  ",
            "nro_afiliado": "  AF-001 (ficticio)  ",
        },
        headers=_headers(token_de(admin)),
    )

    assert respuesta.status_code == 201
    assert respuesta.json() == {
        "id": 1,
        "nombre": "Ana",
        "apellido": "Pérez",
        "dni": "30111222 (ficticio)",
        "telefono": "3884000001",
        "obra_social": "Obra Social Norte (ficticia)",
        "nro_afiliado": "AF-001 (ficticio)",
    }


def test_post_pacientes_alta_valida_sin_opcionales(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)

    respuesta = cliente.post(
        "/pacientes",
        json={
            "nombre": "Ana",
            "apellido": "Pérez",
            "dni": "30111222 (ficticio)",
        },
        headers=_headers(token_de(recepcion)),
    )

    assert respuesta.status_code == 201
    assert respuesta.json() == {
        "id": 1,
        "nombre": "Ana",
        "apellido": "Pérez",
        "dni": "30111222 (ficticio)",
        "telefono": None,
        "obra_social": None,
        "nro_afiliado": None,
    }


def test_post_pacientes_normaliza_dni_con_espacios(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)

    respuesta = cliente.post(
        "/pacientes",
        json={
            "nombre": "Ana",
            "apellido": "Pérez",
            "dni": "   30111222 (ficticio)   ",
        },
        headers=_headers(token_de(recepcion)),
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["dni"] == "30111222 (ficticio)"


def test_post_pacientes_con_nombre_vacio_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))

    respuesta = cliente.post(
        "/pacientes",
        json={
            "nombre": "",
            "apellido": "Pérez",
            "dni": "30111222 (ficticio)",
        },
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/pacientes", headers=cabeceras).json() == []


def test_post_pacientes_con_nombre_solo_espacios_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))

    respuesta = cliente.post(
        "/pacientes",
        json={
            "nombre": "   ",
            "apellido": "Pérez",
            "dni": "30111222 (ficticio)",
        },
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/pacientes", headers=cabeceras).json() == []


def test_post_pacientes_con_apellido_vacio_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))

    respuesta = cliente.post(
        "/pacientes",
        json={
            "nombre": "Ana",
            "apellido": "",
            "dni": "30111222 (ficticio)",
        },
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/pacientes", headers=cabeceras).json() == []


def test_post_pacientes_con_apellido_solo_espacios_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))

    respuesta = cliente.post(
        "/pacientes",
        json={
            "nombre": "Ana",
            "apellido": "   ",
            "dni": "30111222 (ficticio)",
        },
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/pacientes", headers=cabeceras).json() == []


def test_post_pacientes_con_dni_vacio_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))

    respuesta = cliente.post(
        "/pacientes",
        json={
            "nombre": "Ana",
            "apellido": "Pérez",
            "dni": "",
        },
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/pacientes", headers=cabeceras).json() == []


def test_post_pacientes_con_dni_solo_espacios_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))

    respuesta = cliente.post(
        "/pacientes",
        json={
            "nombre": "Ana",
            "apellido": "Pérez",
            "dni": "   ",
        },
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/pacientes", headers=cabeceras).json() == []


def test_post_pacientes_con_dni_duplicado_responde_409_sin_repetir_el_dni(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))
    dni_repetido = "30111222 (ficticio)"
    _crear_paciente(cliente, cabeceras, dni=dni_repetido)

    respuesta = cliente.post(
        "/pacientes",
        json={
            "nombre": "Luis",
            "apellido": "Gómez",
            "dni": dni_repetido,
        },
        headers=cabeceras,
    )

    assert respuesta.status_code == 409
    cuerpo = respuesta.json()
    assert cuerpo.keys() == {"codigo", "mensaje"}
    assert cuerpo["codigo"] == "dni_duplicado"
    assert dni_repetido not in cuerpo["mensaje"]
    assert "30111222" not in cuerpo["mensaje"]
    assert len(cliente.get("/pacientes", headers=cabeceras).json()) == 1


def test_post_pacientes_con_nro_afiliado_sin_obra_social_responde_201(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)

    respuesta = cliente.post(
        "/pacientes",
        json={
            "nombre": "Ana",
            "apellido": "Pérez",
            "dni": "30111222 (ficticio)",
            "nro_afiliado": "AF-999 (ficticio)",
        },
        headers=_headers(token_de(recepcion)),
    )

    assert respuesta.status_code == 201
    assert respuesta.json() == {
        "id": 1,
        "nombre": "Ana",
        "apellido": "Pérez",
        "dni": "30111222 (ficticio)",
        "telefono": None,
        "obra_social": None,
        "nro_afiliado": "AF-999 (ficticio)",
    }


def test_get_pacientes_devuelve_listado_ordenado_por_id(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    primero = _crear_paciente(
        cliente, cabeceras, nombre="Ana", apellido="Pérez", dni="30111222 (ficticio)"
    )
    segundo = _crear_paciente(
        cliente, cabeceras, nombre="Luis", apellido="Gómez", dni="30222333 (ficticio)"
    )

    respuesta = cliente.get("/pacientes", headers=cabeceras)

    assert respuesta.status_code == 200
    assert respuesta.json() == [primero, segundo]


def test_recepcion_get_pacientes_responde_200(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    creado = _crear_paciente(cliente, _headers(token_de(admin)))
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)

    respuesta = cliente.get("/pacientes", headers=_headers(token_de(recepcion)))

    assert respuesta.status_code == 200
    assert respuesta.json() == [creado]


def test_odontologo_get_pacientes_recibe_403(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    odontologo = crear_usuario("odontologo_ficticio", rol=Rol.ODONTOLOGO)

    respuesta = cliente.get("/pacientes", headers=_headers(token_de(odontologo)))

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"


def test_recepcion_post_pacientes_responde_201(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)

    respuesta = cliente.post(
        "/pacientes",
        json={
            "nombre": "Ana",
            "apellido": "Pérez",
            "dni": "30111222 (ficticio)",
        },
        headers=_headers(token_de(recepcion)),
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["id"] == 1


def test_odontologo_post_pacientes_recibe_403_y_no_crea_el_paciente(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    odontologo = crear_usuario("odontologo_ficticio", rol=Rol.ODONTOLOGO)

    respuesta = cliente.post(
        "/pacientes",
        json={
            "nombre": "Ana",
            "apellido": "Pérez",
            "dni": "30111222 (ficticio)",
        },
        headers=_headers(token_de(odontologo)),
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"
    assert cliente.get("/pacientes", headers=_headers(token_de(admin))).json() == []


def test_get_pacientes_sin_token_responde_401(cliente: TestClient) -> None:
    respuesta = cliente.get("/pacientes")

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"


def test_post_pacientes_sin_token_responde_401(cliente: TestClient) -> None:
    respuesta = cliente.post(
        "/pacientes",
        json={
            "nombre": "Ana",
            "apellido": "Pérez",
            "dni": "30111222 (ficticio)",
        },
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"


def test_patch_pacientes_actualiza_nombre_apellido_y_dni(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))
    creado = _crear_paciente(cliente, cabeceras)

    respuesta = cliente.patch(
        f"/pacientes/{creado['id']}",
        json={
            "nombre": "  Ana María  ",
            "apellido": "  Pérez López  ",
            "dni": "  30999888 (ficticio)  ",
        },
        headers=cabeceras,
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "id": creado["id"],
        "nombre": "Ana María",
        "apellido": "Pérez López",
        "dni": "30999888 (ficticio)",
        "telefono": None,
        "obra_social": None,
        "nro_afiliado": None,
    }


def test_patch_pacientes_actualiza_telefono_obra_social_y_nro_afiliado(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))
    creado = _crear_paciente(cliente, cabeceras)

    respuesta = cliente.patch(
        f"/pacientes/{creado['id']}",
        json={
            "telefono": "  3884123456  ",
            "obra_social": "  Obra Social Centro (ficticia)  ",
            "nro_afiliado": "  AF-777 (ficticio)  ",
        },
        headers=cabeceras,
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "id": creado["id"],
        "nombre": "Ana",
        "apellido": "Pérez",
        "dni": "30111222 (ficticio)",
        "telefono": "3884123456",
        "obra_social": "Obra Social Centro (ficticia)",
        "nro_afiliado": "AF-777 (ficticio)",
    }


def test_patch_pacientes_limpia_telefono_con_null(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))
    creado = _crear_paciente(
        cliente,
        cabeceras,
        telefono="3884123456",
        obra_social="Obra Social Centro (ficticia)",
        nro_afiliado="AF-777 (ficticio)",
    )

    respuesta = cliente.patch(
        f"/pacientes/{creado['id']}",
        json={"telefono": None},
        headers=cabeceras,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["telefono"] is None
    assert respuesta.json()["obra_social"] == "Obra Social Centro (ficticia)"
    assert respuesta.json()["nro_afiliado"] == "AF-777 (ficticio)"


def test_patch_pacientes_limpia_obra_social_con_null(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))
    creado = _crear_paciente(
        cliente,
        cabeceras,
        telefono="3884123456",
        obra_social="Obra Social Centro (ficticia)",
        nro_afiliado="AF-777 (ficticio)",
    )

    respuesta = cliente.patch(
        f"/pacientes/{creado['id']}",
        json={"obra_social": None},
        headers=cabeceras,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["obra_social"] is None
    assert respuesta.json()["telefono"] == "3884123456"
    assert respuesta.json()["nro_afiliado"] == "AF-777 (ficticio)"


def test_patch_pacientes_limpia_nro_afiliado_con_null(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))
    creado = _crear_paciente(
        cliente,
        cabeceras,
        telefono="3884123456",
        obra_social="Obra Social Centro (ficticia)",
        nro_afiliado="AF-777 (ficticio)",
    )

    respuesta = cliente.patch(
        f"/pacientes/{creado['id']}",
        json={"nro_afiliado": None},
        headers=cabeceras,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["nro_afiliado"] is None
    assert respuesta.json()["telefono"] == "3884123456"
    assert respuesta.json()["obra_social"] == "Obra Social Centro (ficticia)"


def test_patch_pacientes_con_nombre_null_responde_422_sin_modificar(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))
    creado = _crear_paciente(cliente, cabeceras)

    respuesta = cliente.patch(
        f"/pacientes/{creado['id']}",
        json={"nombre": None},
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/pacientes", headers=cabeceras).json() == [creado]


def test_patch_pacientes_con_apellido_null_responde_422_sin_modificar(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))
    creado = _crear_paciente(cliente, cabeceras)

    respuesta = cliente.patch(
        f"/pacientes/{creado['id']}",
        json={"apellido": None},
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/pacientes", headers=cabeceras).json() == [creado]


def test_patch_pacientes_con_dni_null_responde_422_sin_modificar(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))
    creado = _crear_paciente(cliente, cabeceras)

    respuesta = cliente.patch(
        f"/pacientes/{creado['id']}",
        json={"dni": None},
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/pacientes", headers=cabeceras).json() == [creado]


def test_patch_pacientes_con_nombre_solo_espacios_responde_422_sin_modificar(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))
    creado = _crear_paciente(cliente, cabeceras)

    respuesta = cliente.patch(
        f"/pacientes/{creado['id']}",
        json={"nombre": "   "},
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/pacientes", headers=cabeceras).json() == [creado]


def test_patch_pacientes_con_apellido_solo_espacios_responde_422_sin_modificar(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))
    creado = _crear_paciente(cliente, cabeceras)

    respuesta = cliente.patch(
        f"/pacientes/{creado['id']}",
        json={"apellido": "   "},
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/pacientes", headers=cabeceras).json() == [creado]


def test_patch_pacientes_con_dni_solo_espacios_responde_422_sin_modificar(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))
    creado = _crear_paciente(cliente, cabeceras)

    respuesta = cliente.patch(
        f"/pacientes/{creado['id']}",
        json={"dni": "   "},
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/pacientes", headers=cabeceras).json() == [creado]


def test_patch_pacientes_con_el_mismo_dni_del_paciente_responde_200_sin_conflicto(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))
    creado = _crear_paciente(cliente, cabeceras, dni="30111222 (ficticio)")

    respuesta = cliente.patch(
        f"/pacientes/{creado['id']}",
        json={"dni": "30111222 (ficticio)"},
        headers=cabeceras,
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == creado


def test_patch_pacientes_a_dni_de_otro_paciente_responde_409_sin_repetir_el_dni_y_conserva_el_anterior(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))
    dni_ajeno = "30111222 (ficticio)"
    _crear_paciente(cliente, cabeceras, dni=dni_ajeno)
    segundo = _crear_paciente(
        cliente, cabeceras, nombre="Luis", apellido="Gómez", dni="30222333 (ficticio)"
    )

    respuesta = cliente.patch(
        f"/pacientes/{segundo['id']}",
        json={"dni": dni_ajeno},
        headers=cabeceras,
    )

    assert respuesta.status_code == 409
    cuerpo = respuesta.json()
    assert cuerpo.keys() == {"codigo", "mensaje"}
    assert cuerpo["codigo"] == "dni_duplicado"
    assert dni_ajeno not in cuerpo["mensaje"]
    assert "30111222" not in cuerpo["mensaje"]
    assert cliente.get("/pacientes", headers=cabeceras).json()[1] == segundo


def test_patch_pacientes_inexistente_responde_404(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)

    respuesta = cliente.patch(
        "/pacientes/9999",
        json={"nombre": "Ana"},
        headers=_headers(token_de(recepcion)),
    )

    assert respuesta.status_code == 404
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "no_encontrado"
    assert isinstance(cuerpo["mensaje"], str)
    assert cuerpo["mensaje"].strip() != ""


def test_recepcion_patch_pacientes_responde_200(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    creado = _crear_paciente(cliente, _headers(token_de(admin)))
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)

    respuesta = cliente.patch(
        f"/pacientes/{creado['id']}",
        json={"telefono": "3884000099"},
        headers=_headers(token_de(recepcion)),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["telefono"] == "3884000099"


def test_odontologo_patch_pacientes_recibe_403_y_no_modifica(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras_admin = _headers(token_de(admin))
    creado = _crear_paciente(cliente, cabeceras_admin)
    odontologo = crear_usuario("odontologo_ficticio", rol=Rol.ODONTOLOGO)

    respuesta = cliente.patch(
        f"/pacientes/{creado['id']}",
        json={"nombre": "Modificado"},
        headers=_headers(token_de(odontologo)),
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"
    assert cliente.get("/pacientes", headers=cabeceras_admin).json() == [creado]


def test_patch_pacientes_sin_token_responde_401(cliente: TestClient) -> None:
    respuesta = cliente.patch("/pacientes/1", json={"nombre": "Ana"})

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"
