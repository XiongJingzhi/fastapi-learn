import uuid
from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, ItemServiceDep
from app.models import ItemPublic, ItemsPublic

router = APIRouter()


@router.get("/", response_model=ItemsPublic)
def read_items(
    service: ItemServiceDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """Retrieve items."""
    items, count = service.read_items(current_user=current_user, skip=skip, limit=limit)
    return ItemsPublic(data=items, count=count)


@router.get("/{id}", response_model=ItemPublic)
def read_item(service: ItemServiceDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """Get item by ID."""
    return service.read_item(current_user=current_user, item_id=id)
