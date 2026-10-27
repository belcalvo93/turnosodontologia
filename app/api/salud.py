"""Router de salud: público, sin autenticación y sin tocar la base (C-01)."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Indica que la API está operativa."""
    return {"status": "ok"}
