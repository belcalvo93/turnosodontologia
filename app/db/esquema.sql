-- Esquema de la base SQLite.
--
-- Cada change que necesite persistencia agrega sus tablas acá usando:
--
--     CREATE TABLE IF NOT EXISTS <nombre> (...);
--
-- Así inicializar_esquema() puede reaplicar el archivo en cada arranque sin
-- error. No hay sistema de migraciones: los cambios de columnas se resuelven
-- a mano sobre la base existente.

-- Usuarios del sistema y su rol (C-03, KB 04 §Usuario). La contraseña se guarda
-- solo como hash Argon2id, nunca en texto plano (RN-ACC-04).
CREATE TABLE IF NOT EXISTS usuario (
    id             INTEGER PRIMARY KEY,
    username       TEXT    NOT NULL UNIQUE,
    password_hash  TEXT    NOT NULL,
    rol            TEXT    NOT NULL CHECK (rol IN ('administracion', 'recepcion', 'odontologo')),
    -- Sin FK a propósito y de forma definitiva: SQLite no permite agregar una FK a una
    -- tabla existente sin rehacerla y no hay migraciones. C-07 valida en la aplicación
    -- que el profesional exista al crear o editar un usuario odontólogo.
    profesional_id INTEGER NULL,
    activo         INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);

-- Profesionales del consultorio (C-04, KB 04 §Profesional). Baja lógica con activo = 0.
CREATE TABLE IF NOT EXISTS profesional (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre    TEXT    NOT NULL CHECK (length(trim(nombre)) > 0),
    apellido  TEXT    NOT NULL CHECK (length(trim(apellido)) > 0),
    matricula TEXT    NULL,
    activo    INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);

-- Bloqueos horarios de profesional o sillón (C-09, KB 04 §Bloqueo, RN-REC-02).
CREATE TABLE IF NOT EXISTS bloqueo (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    alcance    TEXT    NOT NULL CHECK (alcance IN ('profesional', 'sillon')),
    recurso_id INTEGER NOT NULL,
    inicio     TEXT    NOT NULL,
    fin        TEXT    NOT NULL,
    motivo     TEXT    NOT NULL DEFAULT '',
    CHECK (inicio < fin)
);

CREATE INDEX IF NOT EXISTS idx_bloqueo_alcance_recurso_inicio
    ON bloqueo (alcance, recurso_id, inicio);
