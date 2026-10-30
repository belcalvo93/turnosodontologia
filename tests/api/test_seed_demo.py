"""Tests del seed demo completo (`sembrar_demo`) y su integración en el arranque (C-17)."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest

from app.db.conexion import abrir_conexion, inicializar_esquema
from app.db.repositorio import insertar_usuario
from app.db.seed import DatosDemo, sembrar_demo
from app.domain.usuarios import Rol

HASH_ADMIN_FICTICIO = "$argon2id$v=19$m=65536,t=3,p=4$hash-admin-ficticio"
HASH_RECEPCION_FICTICIO = "$argon2id$v=19$m=65536,t=3,p=4$hash-recepcion-ficticio"
HASH_ODONTOLOGO_FICTICIO = "$argon2id$v=19$m=65536,t=3,p=4$hash-odontologo-ficticio"
OTRO_HASH_FICTICIO = "$argon2id$v=19$m=65536,t=3,p=4$otro-hash-ficticio"


@pytest.fixture
def conexion(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    ruta = tmp_path / "seed_demo.db"
    inicializar_esquema(ruta)
    with closing(abrir_conexion(ruta)) as conexion_db:
        yield conexion_db


def _sembrar_completo(conexion: sqlite3.Connection) -> DatosDemo:
    return sembrar_demo(
        conexion,
        password_hash_admin=HASH_ADMIN_FICTICIO,
        password_hash_recepcion=HASH_RECEPCION_FICTICIO,
        password_hash_odontologo=HASH_ODONTOLOGO_FICTICIO,
    )


def test_sembrar_demo_crea_catalogo_completo_con_duraciones_matriculas_y_obra_social(
    conexion: sqlite3.Connection,
) -> None:
    datos = _sembrar_completo(conexion)

    profesionales = conexion.execute(
        "SELECT id, nombre, apellido, matricula, activo FROM profesional ORDER BY id"
    ).fetchall()
    assert len(profesionales) == 2
    assert profesionales[0] == (
        datos.profesional_a,
        "Odontólogo",
        "Ficticio A",
        "0001 (ficticia)",
        1,
    )
    assert profesionales[1] == (
        datos.profesional_b,
        "Odontóloga",
        "Ficticia B",
        "0002 (ficticia)",
        1,
    )
    assert all(
        matricula is not None and str(matricula).endswith("(ficticia)")
        for _, _, _, matricula, _ in profesionales
    )

    sillones = conexion.execute(
        "SELECT id, nombre, activo FROM sillon ORDER BY id"
    ).fetchall()
    assert sillones == [
        (datos.sillon_1, "Sillón 1", 1),
        (datos.sillon_2, "Sillón 2", 1),
    ]

    prestaciones = conexion.execute(
        "SELECT id, nombre, duracion_minutos, activa FROM prestacion ORDER BY id"
    ).fetchall()
    assert prestaciones == [
        (datos.consulta, "Consulta ficticia", 30, 1),
        (datos.limpieza, "Limpieza ficticia", 45, 1),
        (datos.tratamiento, "Tratamiento ficticio", 60, 1),
    ]
    assert [duracion for _, _, duracion, _ in prestaciones] == [30, 45, 60]

    pacientes = conexion.execute(
        "SELECT id, nombre, apellido, dni, obra_social FROM paciente ORDER BY id"
    ).fetchall()
    assert len(pacientes) == 2
    assert pacientes[0] == (
        datos.paciente_1,
        "Paciente",
        "Ficticio 1",
        "00000001 (ficticio)",
        "Obra Social Ficticia A",
    )
    assert pacientes[1] == (
        datos.paciente_2,
        "Paciente",
        "Ficticio 2",
        "00000002 (ficticio)",
        None,
    )
    obras_sociales = [obra_social for _, _, _, _, obra_social in pacientes]
    assert any(os is not None for os in obras_sociales)
    assert any(os is None for os in obras_sociales)


def test_sembrar_demo_crea_veinte_horarios_lunes_a_viernes_para_ambos_profesionales(
    conexion: sqlite3.Connection,
) -> None:
    datos = _sembrar_completo(conexion)

    horarios = conexion.execute(
        "SELECT profesional_id, dia_semana, hora_desde, hora_hasta "
        "FROM horario_atencion ORDER BY profesional_id, dia_semana, hora_desde"
    ).fetchall()
    esperados = [
        (prof_id, dia, desde, hasta)
        for prof_id in (datos.profesional_a, datos.profesional_b)
        for dia in range(5)
        for desde, hasta in (("09:00", "13:00"), ("14:00", "18:00"))
    ]
    assert len(horarios) == 20
    assert horarios == esperados


def test_sembrar_demo_vincula_odontologo_demo_al_profesional_a_y_guarda_hashes_argon2id(
    conexion: sqlite3.Connection,
) -> None:
    datos = _sembrar_completo(conexion)

    usuarios = conexion.execute(
        "SELECT id, username, password_hash, rol, profesional_id, activo "
        "FROM usuario ORDER BY id"
    ).fetchall()
    assert usuarios == [
        (datos.admin_demo, "admin_demo", HASH_ADMIN_FICTICIO, "administracion", None, 1),
        (
            datos.recepcion_demo,
            "recepcion_demo",
            HASH_RECEPCION_FICTICIO,
            "recepcion",
            None,
            1,
        ),
        (
            datos.odontologo_demo,
            "odontologo_demo",
            HASH_ODONTOLOGO_FICTICIO,
            "odontologo",
            datos.profesional_a,
            1,
        ),
    ]
    assert all(str(h).startswith("$argon2id$") for _, _, h, _, _, _ in usuarios)


def test_sembrar_demo_no_crea_usuarios_sin_su_contrasena(
    conexion: sqlite3.Connection,
) -> None:
    datos = sembrar_demo(
        conexion,
        password_hash_admin=HASH_ADMIN_FICTICIO,
        password_hash_recepcion=None,
        password_hash_odontologo=None,
    )

    usernames = [
        fila[0]
        for fila in conexion.execute("SELECT username FROM usuario ORDER BY id").fetchall()
    ]
    assert usernames == ["admin_demo"]
    assert datos.recepcion_demo is None
    assert datos.odontologo_demo is None


def test_un_usuario_demo_existente_no_se_modifica(
    conexion: sqlite3.Connection,
) -> None:
    insertar_usuario(
        conexion,
        username="recepcion_demo",
        password_hash=OTRO_HASH_FICTICIO,
        rol=Rol.ADMINISTRACION,
        activo=False,
    )

    _sembrar_completo(conexion)

    fila = conexion.execute(
        "SELECT username, password_hash, rol, profesional_id, activo "
        "FROM usuario WHERE username = ?",
        ("recepcion_demo",),
    ).fetchone()
    assert fila == ("recepcion_demo", OTRO_HASH_FICTICIO, "administracion", None, 0)


def test_datos_ficticios_rotulados_en_pacientes_y_profesionales(
    conexion: sqlite3.Connection,
) -> None:
    _sembrar_completo(conexion)

    dnis = [
        fila[0] for fila in conexion.execute("SELECT dni FROM paciente ORDER BY id").fetchall()
    ]
    assert len(dnis) == 2
    assert all(str(dni).endswith("(ficticio)") for dni in dnis)

    personas = conexion.execute(
        "SELECT nombre, apellido FROM profesional "
        "UNION ALL "
        "SELECT nombre, apellido FROM paciente"
    ).fetchall()
    assert len(personas) == 4
    for nombre, apellido in personas:
        texto = f"{nombre} {apellido}".lower()
        assert "ficticio" in texto or "ficticia" in texto


# --- Arranque (lifespan de create_app) ---


@pytest.fixture
def entorno_tres_claves_demo() -> dict[str, str]:
    """Variables de entorno ficticias de desarrollo para los tests de arranque."""
    return {
        "APP_ENV": "development",
        "SEED_ADMIN_PASSWORD": "clave-admin-demo-ficticia",
        "SEED_RECEPCION_PASSWORD": "clave-recepcion-demo-ficticia",
        "SEED_ODONTOLOGO_PASSWORD": "clave-odontologo-demo-ficticia",
    }


def _config_arranque_demo(ruta_base: Path, entorno: dict[str, str]):  # type: ignore[no-untyped-def]
    from app.config import cargar_config

    return cargar_config(entorno={"DATABASE_URL": str(ruta_base), **entorno})


def _conteos_por_tabla(ruta_base: Path) -> dict[str, int]:
    consultas = {
        "profesional": "SELECT COUNT(*) FROM profesional",
        "sillon": "SELECT COUNT(*) FROM sillon",
        "prestacion": "SELECT COUNT(*) FROM prestacion",
        "horario_atencion": "SELECT COUNT(*) FROM horario_atencion",
        "paciente": "SELECT COUNT(*) FROM paciente",
        "usuario": "SELECT COUNT(*) FROM usuario",
    }
    with closing(abrir_conexion(ruta_base)) as conexion_db:
        return {
            tabla: int(conexion_db.execute(sql).fetchone()[0])
            for tabla, sql in consultas.items()
        }


def test_arranque_con_las_tres_contrasenas_crea_los_tres_usuarios_el_catalogo_y_permite_login(
    tmp_path: Path, entorno_tres_claves_demo: dict[str, str]
) -> None:
    from fastapi.testclient import TestClient
    from app.main import create_app

    ruta = tmp_path / "arranque_completo.db"
    config = _config_arranque_demo(ruta, entorno_tres_claves_demo)

    with TestClient(create_app(config)) as cliente:
        for username, password in (
            ("admin_demo", config.seed_admin_password),
            ("recepcion_demo", config.seed_recepcion_password),
            ("odontologo_demo", config.seed_odontologo_password),
        ):
            respuesta = cliente.post(
                "/auth/login", json={"username": username, "password": password}
            )
            assert respuesta.status_code == 200

    conteos = _conteos_por_tabla(ruta)
    assert conteos == {
        "profesional": 2,
        "sillon": 2,
        "prestacion": 3,
        "horario_atencion": 20,
        "paciente": 2,
        "usuario": 3,
    }
    assert sum(conteos.values()) == 32


def test_dos_arranques_en_development_dejan_exactamente_32_filas_y_los_mismos_hashes(
    tmp_path: Path, entorno_tres_claves_demo: dict[str, str]
) -> None:
    from fastapi.testclient import TestClient
    from app.main import create_app

    ruta = tmp_path / "arranque_idempotente.db"
    config = _config_arranque_demo(ruta, entorno_tres_claves_demo)

    with TestClient(create_app(config)):
        pass
    with closing(abrir_conexion(ruta)) as con:
        hashes_primer_arranque = con.execute(
            "SELECT username, password_hash FROM usuario ORDER BY id"
        ).fetchall()

    with TestClient(create_app(config)):
        pass
    with closing(abrir_conexion(ruta)) as con:
        hashes_segundo_arranque = con.execute(
            "SELECT username, password_hash FROM usuario ORDER BY id"
        ).fetchall()

    conteos = _conteos_por_tabla(ruta)
    assert sum(conteos.values()) == 32
    assert len(hashes_primer_arranque) == 3
    assert hashes_segundo_arranque == hashes_primer_arranque


def test_arranque_solo_con_seed_admin_password_siembra_catalogo_y_no_crea_odontologo_ni_recepcion(
    tmp_path: Path, entorno_tres_claves_demo: dict[str, str]
) -> None:
    from fastapi.testclient import TestClient
    from app.main import create_app

    ruta = tmp_path / "arranque_solo_admin.db"
    config = _config_arranque_demo(
        ruta,
        {
            "APP_ENV": "development",
            "SEED_ADMIN_PASSWORD": entorno_tres_claves_demo["SEED_ADMIN_PASSWORD"],
        },
    )

    with TestClient(create_app(config)):
        pass

    with closing(abrir_conexion(ruta)) as con:
        usernames = [
            f[0] for f in con.execute("SELECT username FROM usuario ORDER BY id").fetchall()
        ]
    conteos = _conteos_por_tabla(ruta)
    assert usernames == ["admin_demo"]
    assert "odontologo_demo" not in usernames
    assert "recepcion_demo" not in usernames
    assert conteos == {
        "profesional": 2,
        "sillon": 2,
        "prestacion": 3,
        "horario_atencion": 20,
        "paciente": 2,
        "usuario": 1,
    }


@pytest.mark.parametrize("app_env", ["test", "production"])
def test_arranque_fuera_de_development_no_siembra_nada(
    tmp_path: Path, app_env: str, entorno_tres_claves_demo: dict[str, str]
) -> None:
    from fastapi.testclient import TestClient
    from app.main import create_app

    ruta = tmp_path / f"arranque_{app_env}.db"
    entorno = {
        **entorno_tres_claves_demo,
        "APP_ENV": app_env,
        "JWT_SECRET": "secreto-ficticio-de-test-con-32-caracteres-o-mas",
    }
    config = _config_arranque_demo(ruta, entorno)

    with TestClient(create_app(config)):
        pass

    assert sum(_conteos_por_tabla(ruta).values()) == 0


def test_arranque_sin_seed_admin_password_no_siembra_nada(
    tmp_path: Path, entorno_tres_claves_demo: dict[str, str]
) -> None:
    from fastapi.testclient import TestClient
    from app.main import create_app

    ruta = tmp_path / "arranque_sin_admin.db"
    entorno = {
        "APP_ENV": "development",
        "SEED_RECEPCION_PASSWORD": entorno_tres_claves_demo["SEED_RECEPCION_PASSWORD"],
        "SEED_ODONTOLOGO_PASSWORD": entorno_tres_claves_demo["SEED_ODONTOLOGO_PASSWORD"],
    }
    config = _config_arranque_demo(ruta, entorno)

    with TestClient(create_app(config)):
        pass

    assert sum(_conteos_por_tabla(ruta).values()) == 0
