import uuid

from fastapi import APIRouter

from app.api.deps import CurrentUser, ItemServiceDep
from app.models import ItemCreate, ItemPublic, ItemUpdate, Message

router = APIRouter()


@router.post("/", response_model=ItemPublic)
def create_item(
    *, service: ItemServiceDep, current_user: CurrentUser, item_in: ItemCreate
) -> ItemPublic:
    """Create new item."""
    return ItemPublic.model_validate(service.create_item(current_user=current_user, item_in=item_in))


@router.put("/{id}", response_model=ItemPublic)
def update_item(
    *,
    service: ItemServiceDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    item_in: ItemUpdate,
) -> ItemPublic:
    """Update an item."""
    updated_item = service.update_item(
        current_user=current_user, item_id=id, item_in=item_in
    )
    return ItemPublic.model_validate(updated_item)


@router.delete("/{id}")
def delete_item(
    service: ItemServiceDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """Delete an item."""
    service.delete_item(current_user=current_user, item_id=id)
    return Message(message="Item deleted successfully")
