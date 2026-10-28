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
