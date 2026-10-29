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

-- Sillones/boxes del consultorio (C-05, KB 04 §Sillon). Baja lógica con activo = 0.
-- RN-REC-01: nombre único.
CREATE TABLE IF NOT EXISTS sillon (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT    NOT NULL UNIQUE CHECK (length(trim(nombre)) > 0),
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);

-- Prestaciones con duración en minutos (C-05, KB 04 §Prestacion). RN-REC-01:
-- nombre único y duración entera mayor que cero. Baja lógica con activa = 0.
CREATE TABLE IF NOT EXISTS prestacion (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre           TEXT    NOT NULL UNIQUE CHECK (length(trim(nombre)) > 0),
    duracion_minutos INTEGER NOT NULL CHECK (duracion_minutos > 0),
    activa           INTEGER NOT NULL DEFAULT 1 CHECK (activa IN (0, 1))
);


-- Pacientes del consultorio (C-06, KB 04 §Paciente). RN-PAC-01, RN-PAC-02:
-- nombre, apellido y DNI obligatorios; DNI único; sin baja lógica.
CREATE TABLE IF NOT EXISTS paciente (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    apellido      TEXT NOT NULL CHECK (length(trim(apellido)) > 0),
    dni           TEXT NOT NULL UNIQUE CHECK (length(trim(dni)) > 0),
    telefono      TEXT NULL,
    obra_social   TEXT NULL,
    nro_afiliado  TEXT NULL
);

-- Horarios de atención de profesionales (C-08, KB 04 §HorarioAtencion, RN-PRO-01/02).
CREATE TABLE IF NOT EXISTS horario_atencion (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    profesional_id INTEGER NOT NULL REFERENCES profesional(id),
    dia_semana     INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 6),
    hora_desde     TEXT    NOT NULL,
    hora_hasta     TEXT    NOT NULL,
    CHECK (hora_desde < hora_hasta)
);

CREATE INDEX IF NOT EXISTS idx_horario_profesional_dia
    ON horario_atencion (profesional_id, dia_semana);
