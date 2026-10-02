# Arquitectura Propuesta

## Patrones aplicados

| Patrón | Dónde se usa | Por qué |
|---|---|---|
| Domain model puro | `domain/` sin I/O ni imports de infra | Testeabilidad y mantenibilidad (prioridad P5) |
| Puertos y adaptadores | Repositorios, reloj, notificador, cobros | Cambiar memoria→SQLite o stub→real sin tocar dominio |
| Casos de uso | `application/` (agendar, reprogramar, lista de espera) | Un punto de entrada por flujo, valida rol + reglas |
| Audit log | Decorador/evento en cada cambio de estado | Trazabilidad barata, base futura Ley 26.529 art. 13 |
| Value objects | DNI, matrícula, pieza FDI, franja horaria | Validación en el borde, errores con código RN |

## Estructura de directorios

```
turnosodontologia/
├── domain/
│   ├── paciente.py
│   ├── profesional.py
│   ├── turno.py
│   ├── bloqueo.py
│   ├── lista_espera.py
│   ├── odontograma.py
│   ├── cobro.py
│   └── rules.py
├── application/
│   ├── agendar.py
│   ├── confirmar.py
│   ├── reprogramar.py
│   ├── cancelar.py
│   ├── bloqueos.py
│   ├── lista_espera.py
│   └── cobros.py
├── infrastructure/
│   ├── memory_repo.py
│   ├── sqlite_repo.py
│   ├── clock.py
│   ├── notifier_stub.py
│   └── audit.py
├── knowledge-base/
├── reports/
├── research_notes/
└── tests/
    ├── test_rules_agenda.py
    ├── test_flujos.py
    └── test_caja.py
```

## Seguridad

- Autenticación: no hay en v1.0 (módulo local); el rol viaja como parámetro de contexto y se valida en cada caso de uso.
- Autorización: matriz RBAC de `03_actores_y_roles.md` aplicada en `application/`.
- Validación de input: value objects + códigos RN-XX-NN explícitos.
- Secrets management: no aplica (sin credenciales ni servicios reales en v1.0).

## Variables de entorno

| Variable | Descripción | Ejemplo | Sensible |
|---|---|---|---|
| `TURNOS_REPO` | Backend de persistencia | `memory` / `sqlite` | N |
| `TURNOS_DB_PATH` | Ruta SQLite cuando aplica | `./data/turnos.db` | N |

Sin deploy no hay más infra: `needs_infra = false`.
