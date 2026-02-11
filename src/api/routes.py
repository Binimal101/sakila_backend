from fastapi import APIRouter, Response
from typing import Any

from . import router

# Register routes on the package-level `router` object.
# Keep this module simple so other modules can import `router` from the package.

@router.get("/health")
def health_check() -> Any:
    """Basic health-check endpoint."""
    return {"status": "ok"}


@router.get("/")
def root() -> Any:
    return {"message": "Sakila backend API"}
