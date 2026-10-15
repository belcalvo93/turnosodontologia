# Etapa 5 — Selección de skills (find-skill)

**Fecha:** 15 de octubre de 2026

La skill `find-skill` **solo recomienda**: relevó el ecosistema de skills, propuso una lista priorizada y **la instalación la decidió el equipo**. Este documento registra el criterio, la recomendación completa y la decisión tomada.

---

## Criterio de selección

- **Stack del proyecto:** Python 3.11 + FastAPI + Pydantic + SQLite + pytest (KB 02). Solo se consideran skills que apliquen a ese stack.
- **MVP solo backend, con Strict TDD activo:** no hay frontend (React es etapa posterior), y cada regla RN-xx mapea a ≥1 test, así que el foco está en FastAPI y testing.
- **Preferencia por fuentes oficiales o con muchas instalaciones:** se priorizaron skills de fuentes oficiales (`fastapi/fastapi`, `pydantic/skills`) o con alto número de instalaciones.
- **Sin superposición:** no se instalan skills que dupliquen la funcionalidad de otra ya elegida.

---

## Recomendaciones y decisión

| Skill | Nivel | Instalaciones | ¿Instalada? | Justificación |
|-------|-------|---------------|-------------|---------------|
| `wshobson/agents@python-testing-patterns` | 1 | 35,5K | Sí | Base del Strict TDD: fixtures, parametrización y patrones pytest. |
| `wshobson/agents@fastapi-templates` | 1 | 25,4K | Sí | Scaffolding y estructura para C-01 (app/{domain,api,db}). |
| `fastapi/fastapi@fastapi` | 1 | 12,2K | Sí | Fuente oficial: idioms de FastAPI y Pydantic para todos los routers. |
| `wshobson/agents@auth-implementation-patterns` | 1 | 18,3K | Sí | Cubre C-03 (token, RBAC, hash) y los códigos 401/403. |
| `wshobson/agents@api-design-principles` | 1 | 29,7K | Sí | Convenciones REST alineadas a la KB (409, 422, 403, 401). |
| `mindrally/skills@fastapi-python` | 2 | 13,7K | No | Se superpone con `fastapi/fastapi`, ya instalada. |
| `affaan-m/ecc@fastapi-patterns` | 2 | 6,6K | No | Redundante con `fastapi-templates` y `fastapi`. |
| `jeffallan/claude-skills@fastapi-expert` | 2 | 5,9K | No | Duplica FastAPI + JWT ya cubiertos por las instaladas. |
| `github/awesome-copilot@pytest-coverage` | 2 | 12,8K | No | `python-testing-patterns` ya cubre el testing; cobertura es métrica, no MVP. |
| `getsentry/skills@security-review` | 2 | 19,9K | No | Útil para revisión puntual, pero solapa con `auth-implementation-patterns`. |
| `wshobson/agents@sql-optimization-patterns` | 2 | 19,3K | No | Optimización prematura; la persistencia (SQLite) es provisional (D-01). |
| `wshobson/agents@python-configuration` | 3 | 11,2K | No | `config.py` con env vars se resuelve con la stdlib; no aporta al MVP. |
| `pydantic/skills@pydantic` | 3 | 1,9K | No | Pydantic ya queda cubierto por `fastapi/fastapi`. |
| `martinholovsky/claude-skills-generator@SQLite Database Expert` | 3 | 3,1K | No | SQLite es provisional (D-01); el acceso a datos vive en `app/db`. |
| `coderabbitai/skills@code-review` | 3 | 13,9K | No | Revisión general de código; no aporta al alcance del MVP. |
| `alleneubank/claude-code@python-best-practices` | 3 | 2,1K | No | Reglas genéricas ya cubiertas por las reglas duras del proyecto. |
| `mattpocock/skills@tdd` | Descartada | 1,1M | No | Orientada a TypeScript; el TDD en Python lo cubre `python-testing-patterns`. |

---

## Instaladas (Nivel 1)

- **`wshobson/agents@python-testing-patterns`** — sostiene el **Strict TDD** de todo el camino crítico: los tests de dominio sin DB/HTTP de C-02 y C-10, y los tests de API de C-11 (crear/turno, doble reserva).
- **`wshobson/agents@fastapi-templates`** — aporta la estructura de proyecto que necesita **C-01 `foundation-setup`** (`app/{domain,api,db}` y `tests/`), alineada con la arquitectura de KB 08.
- **`fastapi/fastapi@fastapi`** — fuente oficial; fija los idioms de FastAPI y Pydantic en todos los routers (C-04 a C-16).
- **`wshobson/agents@auth-implementation-patterns`** — cubre **C-03 `auth-login-roles`**: hash con sal (RN-ACC-04), token y el chequeo de rol que produce los **401 sin autenticar** y **403 rol sin permiso** de RN-GLO-01.
- **`wshobson/agents@api-design-principles`** — aporta las convenciones REST y los **códigos 409 conflicto y 422 dato inválido** de RN-GLO-01, consistentes con el mapeo de errores de la KB.

---

## No instaladas (Niveles 2 y 3)

- **`mindrally/skills@fastapi-python`** — se superpone con `fastapi/fastapi`, ya instalada.
- **`affaan-m/ecc@fastapi-patterns`** — redundante con `fastapi-templates` y `fastapi`.
- **`jeffallan/claude-skills@fastapi-expert`** — duplica FastAPI + JWT ya cubiertos.
- **`github/awesome-copilot@pytest-coverage`** — `python-testing-patterns` ya cubre el testing; la cobertura es una métrica, no una necesidad del MVP.
- **`getsentry/skills@security-review`** — útil para una revisión puntual, pero solapa con `auth-implementation-patterns`.
- **`wshobson/agents@sql-optimization-patterns`** — optimización prematura para el tamaño del MVP; SQLite es provisional (D-01).
- **`wshobson/agents@python-configuration`** — `config.py` con variables de entorno se resuelve con la stdlib; no aporta al MVP.
- **`pydantic/skills@pydantic`** — Pydantic ya viene cubierto por `fastapi/fastapi`.
- **`martinholovsky/claude-skills-generator@SQLite Database Expert`** — SQLite es provisional (D-01) y el acceso a datos vive concentrado en `app/db`.
- **`coderabbitai/skills@code-review`** — revisión general de código; no aporta al alcance del MVP.
- **`alleneubank/claude-code@python-best-practices`** — reglas genéricas ya cubiertas por las reglas duras del proyecto.

---

## Descartada

- **`mattpocock/skills@tdd`** — orientada a TypeScript; el TDD en Python lo cubre `python-testing-patterns`.

---

Las skills instaladas y sus reglas compactas quedan registradas en `.atl/skill-registry.md`.
