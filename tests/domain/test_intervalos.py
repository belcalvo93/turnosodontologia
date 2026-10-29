from datetime import datetime

from app.domain.intervalos import es_futuro, solapan
from app.domain.models import Bloqueo, Turno

LUNES = datetime(2026, 10, 19)


def _hora(hh: int, mm: int = 0) -> datetime:
    return LUNES.replace(hour=hh, minute=mm)


def _turno(inicio: datetime, fin: datetime) -> Turno:
    return Turno(
        paciente_id=1,
        profesional_id=1,
        sillon_id=1,
        prestacion_id=1,
        inicio=inicio,
        fin=fin,
    )


def test_turnos_contiguos_no_solapan() -> None:
    a = _turno(_hora(10), _hora(10, 30))
    b = _turno(_hora(10, 30), _hora(11))
    assert solapan(a, b) is False
    assert solapan(b, a) is False


def test_solapamiento_parcial_solapa() -> None:
    a = _turno(_hora(10), _hora(10, 30))
    b = _turno(_hora(10, 15), _hora(10, 45))
    assert solapan(a, b) is True
    assert solapan(b, a) is True


def test_intervalo_contenido_solapa() -> None:
    a = _turno(_hora(10), _hora(12))
    b = _turno(_hora(10, 30), _hora(11))
    assert solapan(a, b) is True
    assert solapan(b, a) is True


def test_intervalos_con_mismo_inicio_solapan() -> None:
    a = _turno(_hora(10), _hora(10, 30))
    b = _turno(_hora(10), _hora(10, 45))
    assert solapan(a, b) is True
    assert solapan(b, a) is True


def test_intervalos_disjuntos_no_solapan() -> None:
    a = _turno(_hora(9), _hora(9, 30))
    b = _turno(_hora(11), _hora(11, 30))
    assert solapan(a, b) is False


def test_turno_y_bloqueo_se_comparan_con_la_misma_regla() -> None:
    bloqueo = Bloqueo(
        alcance="sillon",
        recurso_id=1,
        inicio=_hora(10),
        fin=_hora(12),
        motivo="Mantenimiento ficticio",
    )
    assert solapan(_turno(_hora(11), _hora(11, 30)), bloqueo) is True
    assert solapan(_turno(_hora(12), _hora(12, 30)), bloqueo) is False


def test_es_futuro_con_reloj_antes_del_inicio_devuelve_true() -> None:
    ahora = _hora(9, 0)
    turno = _turno(_hora(10, 0), _hora(10, 30))
    assert es_futuro(turno, ahora) is True


def test_es_futuro_con_reloj_igual_al_inicio_devuelve_false() -> None:
    ahora = _hora(9, 0)
    turno = _turno(_hora(9, 0), _hora(9, 30))
    assert es_futuro(turno, ahora) is False


def test_es_futuro_con_reloj_despues_del_inicio_devuelve_false() -> None:
    ahora = _hora(9, 0)
    turno = _turno(_hora(8, 30), _hora(9, 0))
    assert es_futuro(turno, ahora) is False
