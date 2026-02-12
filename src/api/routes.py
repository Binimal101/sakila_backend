#api
from fastapi import APIRouter, Response, Depends
from typing import Any
from . import router, app

# db
from src.alchemy.db import get_db
from sqlalchemy.orm import Session

# data validation (removed - validation handled elsewhere)


@router.get("/api/health")
def health_check() -> Any:
    """Basic health-check endpoint."""
    return {"status": "ok"}


@router.get("/api")
def root() -> Any:
    return {"message": "Sakila backend API"}

"""
Begin project route dependencies
"""

@router.post("/api/top_5_rentals")
def t5_rentals(db = Depends(get_db)) -> Any:
    """Top 5 rentals (placeholder)."""
    return {"detail": "not implemented"}

@router.post("/api/details/film")
def film_details(db = Depends(get_db)) -> Any:
    """Film details (placeholder)."""
    return {"detail": "not implemented"}

@router.post("/api/top_5_actors")
def t5_actors(db = Depends(get_db)) -> Any:
    """Top 5 actors (placeholder)."""
    return {"detail": "not implemented"}

@router.post("/api/top_n_rentals_with_actor")
def tn_rentals_actor(db = Depends(get_db)) -> Any:
    """Top N rentals for given actor (placeholder)."""
    return {"detail": "not implemented"}

@router.post("/api/query/films")
def query_films(db = Depends(get_db)) -> Any:
    """Query films (placeholder)."""
    return {"detail": "not implemented"}

@router.post("/api/rent")
def rent(db = Depends(get_db)) -> Any:
    """Rent a film (placeholder)."""
    return {"detail": "not implemented"}

@router.post("/api/query/customer")
def query_customer(db = Depends(get_db)) -> Any:
    """Query customer (placeholder)."""
    return {"detail": "not implemented"}

@router.post("/api/customer/create")
def create_customer(db = Depends(get_db)) -> Any:
    """Create customer (placeholder)."""
    return {"detail": "not implemented"}

@router.post("/api/customer/edit")
def edit_customer(db = Depends(get_db)) -> Any:
    """Edit customer (placeholder)."""
    return {"detail": "not implemented"}

@router.post("/api/details/customer")
def customer_details(db = Depends(get_db)) -> Any:
    """Customer details (placeholder)."""
    return {"detail": "not implemented"}

@router.post("/api/return")
def return_(db = Depends(get_db)) -> Any:
    """Return rental (placeholder)."""
    return {"detail": "not implemented"}

app.include_router(router)