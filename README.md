# Turnos Odontológicos

Backend académico para gestionar turnos de un consultorio odontológico (Trabajo de Integración, Metodología I, TUP – UTN FRM). Todos los datos de ejemplo son ficticios.

Desarrollado con Spec-Driven Development usando OpenSpec y Active Stack (ciclo OPSX).

## Estado actual

Implementado el change **C-10 `reglas-alta-turno`**: validación del alta de un turno en dominio puro, sin base de datos ni HTTP.

- Calcula el fin del turno a partir de la duración de la prestación.
- Rechaza turnos fuera del horario de atención del profesional.
- Rechaza turnos dentro de un bloqueo del profesional o del sillón.
- Rechaza solapamientos por profesional, sillón o paciente, con intervalos semiabiertos `[inicio, fin)`: los turnos contiguos son válidos.

## Requisitos

- Git
- Python 3.11 o superior

No hace falta Docker ni base de datos.

## Instalación

```bash
git clone https://github.com/belcalvo93/turnosodontologia.git
cd turnosodontologia
python -m venv .venv
```

Activar el entorno virtual:

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```

> En Windows, si PowerShell muestra "la ejecución de scripts está deshabilitada", correr antes
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` (solo afecta a esa ventana).

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

> En Linux / macOS puede ser necesario usar `python3` en lugar de `python`.

## Correr los tests

Desde la raíz del repositorio, con el entorno virtual activo:

```bash
pytest tests/domain/ -v
```

Resultado esperado: `32 passed`. Los tests de dominio corren sin base de datos ni HTTP.

## Estructura

```
app/domain/                 Lógica de dominio pura (modelos, intervalos, errores y reglas de alta)
tests/domain/               Tests unitarios de dominio (pytest)
knowledge-base/             Base de conocimiento del proyecto (10 archivos)
docs/discovery/             Informe de Discovery y verificación de fuentes
openspec/specs/             Specs vigentes del sistema
openspec/changes/archive/   Changes archivados (proposal, design, specs, tasks y verify)
CHANGES.md                  Roadmap de changes del MVP
AGENTS.md / CLAUDE.md       Reglas para los agentes de IA
```

## Seguridad y datos

- El repositorio no contiene claves ni credenciales.
- Todos los datos de pacientes, profesionales y sillones de los tests son ficticios.