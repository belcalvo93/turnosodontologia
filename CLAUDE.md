# Turnos Odontológicos — Instrucciones para Agentes

> Este archivo (y su copia `CLAUDE.md`) es lo PRIMERO que todo agente lee al entrar al repo.
> Generado a partir de `knowledge-base/`, `CHANGES.md` y `.atl/skill-registry.md`. No editar a mano sin re-sincronizar ambos archivos.

---

## Stack Tecnológico

> **Provisional** — ver decisión D-01 en `knowledge-base/09_decisiones_y_supuestos.md`.

| Capa | Tecnología | Versión mínima |
|------|------------|----------------|
| Lenguaje | Python | 3.11 |
| Framework API | FastAPI (+ Pydantic para validación de entrada/salida) | A definir al crear el proyecto |
| Persistencia | SQLite (provisional) | Incluida con Python |
| Tests | pytest (+ cliente de pruebas de FastAPI / TestClient) | A definir |
| Autenticación | Token firmado (JWT es el candidato; no decidido, ver D-03) | — |
| Despliegue | Local / entorno académico. Docker no es requisito | — |

Detalle completo: [knowledge-base/02_descripcion_general.md](knowledge-base/02_descripcion_general.md)

---

## Base de Conocimiento

La fuente de verdad del dominio vive en `knowledge-base/`. **Leé el archivo relevante ANTES de implementar.**

| Archivo | Cuándo leerlo |
|---------|---------------|
| [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) | Entender propósito y alcance del MVP |
| [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) | Auth, RBAC, permisos |
| [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) | Entidades, ERD, seed data |
| [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) | Reglas codificadas (RN-XX) |
| [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) | Historias de usuario por épica |
| [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) | Flujos extremo a extremo |
| [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) | Patrones, estructura de directorios, env vars |
| [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) | ⚠️ Inconsistencias a resolver ANTES de codear |

> ⚠️ Resolver las preguntas de prioridad **Alta** de `knowledge-base/10_preguntas_abiertas.md` antes de arrancar el primer change: IF-06, SE-01, SE-02, SE-06, SE-09, SE-10 y SE-12.

---

## Skills Disponibles

> Fuente de verdad: `.atl/skill-registry.md` (generado por `skill-registry`). El MVP es solo backend, así que no hay agente de frontend.

> Las skills vienen incluidas en el repositorio (`.agents/skills/` y `.claude/skills/`): **no hace falta instalarlas**. Para restaurarlas o reinstalarlas, usar `npx skills experimental_install`, que lee `skills-lock.json`.

| Agente | Rol | Skills que carga |
|--------|-----|------------------|
| **Dominio y turnos** | Reglas puras de solapamiento/validación, tests de dominio | `python-testing-patterns`, `api-design-principles` |
| **Backend FastAPI** | Routers, Pydantic, scaffolding del proyecto | `fastapi`, `fastapi-templates` |
| **Acceso y seguridad** | Login, token, RBAC, auditoría | `auth-implementation-patterns`, `fastapi` |
| **Orquestación** | Fundación OPSX/SDD y docs | `active-orchestrator`, `kb-creator`, `roadmap-generator`, `agent-instruction`, `skill-registry`, `find-skill`, `skill-creator` |
| **Revisión de specs** | Revisar escenarios, citas RN-xx y tasks.md antes del apply | `revisor-escenarios-sdd` |

> `revisor-escenarios-sdd`: revisar los specs y `tasks.md` de un change AL TERMINAR un `/opsx:propose` y ANTES de `/opsx:apply`. Necesita solo la ruta del change (`openspec/changes/<nombre>/`). Informa hallazgos (ambigüedad, falta, sobra, cita errónea, conteo) con archivo y línea, sin modificar archivos: el humano decide qué corregir.

Cargá la skill correspondiente al contexto ANTES de escribir código.

> Los compact rules de cada skill los resuelve el orquestador desde `.atl/skill-registry.md` (generado por `skill-registry`). Esta tabla solo mapea skill→rol.

---

## Roadmap de Changes

El plan de implementación completo está en [CHANGES.md](CHANGES.md). Resumen:

- **Total**: 17 changes (C-01 a C-17) en 5 fases.
- **Camino crítico** (8): `C-01 → C-03 → C-04 → C-09 → C-11 → C-12 → C-15 → C-17`.
- **Primer change**: `C-01` (`foundation-setup`), governance BAJO, sin dependencias.
- **Cuello de botella**: `C-11 crear-turno` depende de 4 changes y bloquea 5.
- **Bloqueado por decisión**: `C-16` no se propone hasta resolver SE-09.

**Antes de cualquier `/opsx:propose`**: leé [CHANGES.md](CHANGES.md), identificá las dependencias del change y los archivos de "Leer antes".

---

## Reglas Duras (específicas del proyecto)

> Reglas **globales** ya definidas en `~/.claude/CLAUDE.md` (orquestador, reglas de delegación, governance por dominio, Engram, Strict TDD Mode, model assignments): el proyecto las **hereda** y NO se repiten acá. Abajo viven solo las reglas específicas de este proyecto.

Son contrato; romperlas es un defecto.

1. NUNCA importar FastAPI ni nada de `app/db`/`app/api` desde `app/domain/` → el dominio es Python puro. Dependencias: `api → domain + db`; `db → domain` (solo tipos); `domain → nada`. (KB 08)
2. NUNCA llamar `datetime.now()`/`date.today()` dentro del dominio → recibir `ahora` como parámetro (reloj inyectado). (RN-TUR-09)
3. NUNCA usar intervalos cerrados en `solapan()` → intervalos semiabiertos `[inicio, fin)`; los turnos contiguos son válidos. (RN-TUR-04, SE-10)
4. NUNCA concatenar ni interpolar strings en SQL → usar consultas parametrizadas. (KB 08 §Seguridad)
5. NUNCA escribir el turno y su auditoría por separado → validar y escribir ambos en una única transacción. (RN-AUD-03, SE-06)
6. NUNCA hacer UPDATE ni DELETE sobre `auditoria_turno` → solo INSERT (append-only). (RN-AUD-02)
7. NUNCA devolver errores ad-hoc → mapeo global a JSON en español con código: 409 conflicto, 422 dato inválido, 403 rol sin permiso, 401 sin autenticar. (RN-GLO-01)
8. NUNCA poner reglas de negocio en el router → validación de entrada/salida con Pydantic en la frontera; la lógica vive en `app/domain/`. (KB 08)
9. NUNCA versionar `.env` → solo `.env.example` con placeholders; secretos por variable de entorno y contraseñas con hash y sal (bcrypt/argon2), nunca texto plano. (KB 08, RN-ACC-04)
10. NUNCA usar datos reales de pacientes → datos ficticios rotulados, DNI con sufijo "(ficticio)". (KB 01, RN-PAC-03)
11. NUNCA dejar una regla RN-xx sin test → cada RN-xx mapea a ≥1 test; los tests de dominio corren sin base de datos ni HTTP. (KB 01, KB 08)
12. NUNCA romper el estilo → `snake_case` y type hints en todas las funciones públicas (Python 3.11).
13. NUNCA hacer commit ni push sin que el usuario lo pida → mensajes de commit en español, a nombre de cada integrante y sin línea de coautoría de IA.
14. NUNCA modificar `knowledge-base/`, `CHANGES.md`, `docs/discovery/` ni `.active-orchestrator-state.json` sin pedirlo → si una skill propone regenerarlos, PARAR y preguntar. Excepción: los comandos `/opsx:*` sí pueden crear y modificar `openspec/changes/` y `openspec/specs/`, porque es su función.

---

## Flujo de Trabajo

```
1. Leer la KB relevante (knowledge-base/)        → entender el dominio
2. Identificar el change en CHANGES.md           → respetar dependencias
3. /opsx:explore C-NN-nombre                     → relevar el problema antes de proponer
4. /opsx:propose C-NN-nombre                     → proposal + design + specs + tasks (mínimo 3 escenarios dado/cuando/entonces)
5. /opsx:apply C-NN-nombre                       → implementar con Strict TDD, respetando las reglas duras
6. Verify                                        → correr la suite de tests y los health checks; no se archiva con algo en rojo
7. /opsx:archive C-NN-nombre + marcar [x]        → cerrar el change y actualizar los specs
```

Aplicar TODAS las reglas duras en cada paso. Ante conflicto entre la KB y este archivo, las reglas duras prevalecen.
