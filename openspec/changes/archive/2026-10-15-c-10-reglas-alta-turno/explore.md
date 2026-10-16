# Explore — C-10 reglas-alta-turno

> Resumen del relevamiento previo al propose. También guardado en Engram (`Explore C-10 reglas-alta-turno`, topic `opsx/c-10-reglas-alta-turno/explore`).

## Problema

Los consultorios gestionan turnos sin validación que evite solapamientos por profesional/sillón ni controle horario y bloqueos. C-10 concentra esa validación en dominio puro (`validar_alta`), testeable sin DB ni HTTP.

## Estado del repo al relevar

- `main` con etapas 1-5 mergeadas (discovery, KB de 10 archivos, `CHANGES.md`, `AGENTS.md`, skills).
- Sin código: no existe `app/`; `openspec/changes/archive/` y `openspec/specs/` vacíos → C-01 y C-02 sin implementar.
- Decisión: diseñar contra el contrato previsto de C-02 (`Turno`, `Prestacion`, `HorarioAtencion`, `Bloqueo`, `solapan()` semiabierto, errores de dominio). Belén agregó tasks §0 (base técnica mínima) para darle a Joaquín un punto de partida runnable.

## Reglas y supuestos clave

- RN-TUR-01 (fin desde prestación), RN-TUR-03/04 (solape + contiguos `[inicio, fin)`), RN-TUR-05 (bloqueos), RN-TUR-08 (cancelados no cuentan + `excluir_turno_id`), RN-TUR-12 (paciente), RN-PRO-01/02 (franja única).
- Supuestos: SE-02 (todo turno usa sillón), SE-03 (solape por paciente), SE-04 (sin sobreturnos), SE-10 (semiabiertos), SE-14 (no cruza corte).
- `validar_alta` no recibe `ahora` (el futuro se valida en C-12/C-13). Stack: Python 3.11 + PyTest, sin GUI.

## Fuentes

`CHANGES.md` (C-10, FASE 3), `knowledge-base/05`, `08`, `07` (Flujo 2), `10` (SE-02/03/04/10/14), `04` (modelo y seed ficticio).
