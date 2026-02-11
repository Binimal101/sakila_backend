from fastapi import APIRouter
from typing import Any, List

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[dict])
def list_users() -> Any:
    """Return a small sample list of users (replace with DB calls)."""
    return [{"user_id": 1, "name": "Alice"}]


@router.get("/{user_id}")
def get_user(user_id: int) -> Any:
    return {"user_id": user_id, "name": "Alice"}
