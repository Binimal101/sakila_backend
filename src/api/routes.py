#api
from fastapi import APIRouter, Response, Depends
from typing import Any
from . import router, app

#db
from src.alchemy.db import get_db


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
def t5_rentals(Depends(get_db)):
    pass

@router.post("/api/details/film")
def film_details(Depends(get_db)):
    pass

@router.post("/api/top_5_actors")
def t5_actors(Depends(get_db)):
    pass

@router.post("/api/top_n_rentals_with_actor")
def tn_rentals_actor(Depends(get_db)):
    pass

@router.post("/api/query/films")
def query_films(Depends(get_db)):
    pass

@router.post("/api/rent")
def rent(Depends(get_db)):
    pass

@router.post("/api/query/customer")
def query_customer(Depends(get_db)):
    pass

@router.post("/api/customer/create")
def create_customer(Depends(get_db)):
    pass

@router.post("/api/customer/edit")
def edit_customer(Depends(get_db)):
    pass

@router.post("/api/details/customer")
def customer_details(Depends(get_db)):
    pass

@router.post("/api/return")
def return_(Depends(get_db)):
    pass

app.include_router(router)