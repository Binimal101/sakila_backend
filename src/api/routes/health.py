from fastapi import APIRouter
from typing import Any

router = APIRouter(tags=["health"])

@router.get("/health")
def health_check() -> Any:
    """Basic health-check endpoint."""
    return {"status": "ok"}
