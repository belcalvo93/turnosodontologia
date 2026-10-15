# Tasks — C-10 reglas-alta-turno

## 0. Base técnica mínima (C-01 y C-02 reducidos)

- [x] 0.1 Crear la estructura `app/domain/` y `tests/domain/`, `requirements.txt` con pytest y el README con cómo instalar y correr `pytest tests/domain/`, verificando que `pytest` arranca sin errores
- [x] 0.2 Implementar `solapan()` con intervalos semiabiertos, los errores de dominio y los modelos mínimos (`Turno`, `Prestacion`, `HorarioAtencion`, `Bloqueo`), con tests de `solapan()` (contiguos válidos, solapamiento parcial), verificando que pasan

## 1. Función validar_alta y cálculo de fin (RN-TUR-01)

- [x] 1.1 Implementar `validar_alta` con cálculo `fin = inicio + duracion_minutos` y test con prestación ficticia de 45 min (inicio 10:00 → fin 10:45) y de 30 min (→ fin 10:30), verificando que `pytest tests/domain/test_reglas_turno.py` pasa
- [x] 1.2 Validar franja única de atención (RN-PRO-01/02) con tests: turno 12:30-13:00 aceptado y 12:45-13:15 rechazado con `FueraDeHorario`, verificando que ambos tests pasan sin DB ni HTTP

## 2. Bloqueos y solapamientos (RN-TUR-03/04/05/08/12)

- [x] 2.1 Implementar rechazo por bloqueo de profesional/sillón (RN-TUR-05) con tests: bloqueo ficticio de sillón 10:00-12:00 rechaza turno 11:00 en ese sillón y acepta en otro y a las 12:00, verificando que los 3 tests pasan
- [ ] 2.2 Implementar solapamiento por profesional, sillón y paciente con intervalos semiabiertos (RN-TUR-03/04/12) más exclusión de cancelados y `excluir_turno_id` (RN-TUR-08), verificando que `pytest tests/domain/test_reglas_turno.py -k "solapamiento or contiguo or cancelado or excluir"` pasa
- [ ] 2.3 Cubrir el escenario de borde de turnos contiguos 10:00-10:30 y 10:30-11:00 aceptados y 10:29-10:59 rechazado (RN-TUR-04), verificando que los tests de borde pasan

## 3. Verificación de integración del change

- [ ] 3.1 Correr la suite completa de dominio `pytest tests/domain/` y verificar que todo está en verde sin importar FastAPI ni `app/db` desde `app/domain`
