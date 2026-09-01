from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="Health check")
def health_check() -> dict[str, str]:
    """Health check endpoint to verify service availability."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
    }
