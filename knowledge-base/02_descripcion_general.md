# Descripción General

## Tipo de sistema

API REST (backend) para gestión de agenda de turnos de un consultorio odontológico. Para el MVP alcanza con el backend; un frontend mínimo en TypeScript es el change C-18 (posterior al MVP, D-09), y el frontend React completo y la app móvil son etapas posteriores (informe, D.3).

## Stack tecnológico

> **PROVISIONAL**: ver decisión D-01 en [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md).

| Capa | Tecnologías | Versión mínima |
|------|-------------|----------------|
| Lenguaje | Python | 3.11 (Supuesto del equipo) |
| Framework API | FastAPI (+ Pydantic para validación de entrada/salida) | A definir al crear el proyecto |
| Persistencia | SQLite (provisional) | Incluida con Python |
| Tests | pytest (+ cliente de pruebas de FastAPI para tests de API) | A definir |
| Autenticación | Token firmado (JWT es candidato, no decidido; ver D-03) | — |
| Despliegue | Local / entorno académico. Docker no es requisito | — |

## Arquitectura general

Arquitectura simple de cuatro carpetas, con el dominio separado del framework y sin capas extra.

```
Cliente HTTP --> app/api (routers FastAPI) --> app/domain (entidades + reglas puras)
                         |
                         +--> app/db (SQLite: lee/escribe)
```

- `app/domain/`: Python puro (entidades y reglas de solapamiento/validación). No importa FastAPI ni nada de base de datos.
- `app/api/`: routers de FastAPI; traducen HTTP a llamadas al dominio y a `app/db`.
- `app/db/`: persistencia SQLite.
- `tests/`: pytest; los tests de dominio no necesitan base de datos ni HTTP.

Detalle en [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md).

## Integraciones externas

Ninguna en el MVP. Quedan fuera (etapas posteriores, informe D.3): WhatsApp Business API, Mercado Pago, ARCA.

| Servicio | Propósito | Tipo | Estado |
|----------|-----------|------|--------|
| WhatsApp Business API | Recordatorios | REST | Etapa posterior (costo por mensaje, informe resumen ejecutivo) |
| Mercado Pago | Señas | REST/SDK | Etapa posterior |
| ARCA | Facturación electrónica | Web service | Etapa posterior |

## API REST (resumen del MVP, propuesto)

Los nombres de rutas son una propuesta del equipo (**Supuesto del equipo**).

| Recurso | Endpoints principales |
|---------|-----------------------|
| auth | `POST /auth/login` |
| usuarios | `GET/POST /usuarios`, `PATCH /usuarios/{id}` (solo administración, US-013) |
| profesionales | `GET/POST /profesionales`, `PATCH /profesionales/{id}` |
| sillones | `GET/POST /sillones`, `PATCH /sillones/{id}` |
| prestaciones | `GET/POST /prestaciones`, `PATCH /prestaciones/{id}` |
| horarios | `GET/POST /profesionales/{id}/horarios` |
| bloqueos | `GET/POST/DELETE /bloqueos` |
| pacientes | `GET/POST /pacientes`, `PATCH /pacientes/{id}` |
| turnos | `POST /turnos`, `POST /turnos/{id}/cancelar`, `POST /turnos/{id}/reprogramar`, `GET /turnos/{id}` |
| agenda | `GET /agenda/profesionales/{id}?desde&hasta`, `GET /agenda/sillones/{id}?desde&hasta` |
| auditoría | `GET /auditoria?turno_id=` |
| salud | `GET /health` |

Convención de errores (propuesta): 409 para conflictos de solapamiento, 422 para datos inválidos, 403 para rol sin permiso, 401 sin autenticar.
