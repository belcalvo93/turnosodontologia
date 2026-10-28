-- Esquema de la base SQLite.
--
-- Cada change que necesite persistencia agrega sus tablas acá usando:
--
--     CREATE TABLE IF NOT EXISTS <nombre> (...);
--
-- Así inicializar_esquema() puede reaplicar el archivo en cada arranque sin
-- error. No hay sistema de migraciones: los cambios de columnas se resuelven
-- a mano sobre la base existente.

-- Profesionales del consultorio (C-04, KB 04 §Profesional). Baja lógica con activo = 0.
CREATE TABLE IF NOT EXISTS profesional (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre    TEXT    NOT NULL CHECK (length(trim(nombre)) > 0),
    apellido  TEXT    NOT NULL CHECK (length(trim(apellido)) > 0),
    matricula TEXT    NULL,
    activo    INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);
