# Turnos Odontológicos

Backend académico para gestión de turnos de un consultorio odontológico. Todos los datos de ejemplo son ficticios.

## Requisitos

- Python 3.11 o superior

## Instalación

```bash
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## Correr los tests de dominio

Desde la raíz del repositorio:

```bash
pytest tests/domain/
```

Los tests de dominio corren sin base de datos ni HTTP.
