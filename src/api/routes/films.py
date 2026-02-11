from fastapi import APIRouter
from typing import Any, List

router = APIRouter(prefix="/films", tags=["films"])

@router.get("/", response_model=List[dict])
def list_films() -> Any:
    return [{"film_id": 1, "title": "Example Film"}]


@router.get("/{film_id}")
def get_film(film_id: int) -> Any:
    return {"film_id": film_id, "title": "Example Film"}
