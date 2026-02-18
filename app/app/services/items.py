import uuid

from sqlmodel import Session

from app.core.exceptions import PermissionDeniedError, ResourceNotFoundError
from app.crud import items as items_crud
from app.models import Item, ItemCreate, ItemUpdate, User


class ItemService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def read_items(
        self, *, current_user: User, skip: int, limit: int
    ) -> tuple[list[Item], int]:
        if current_user.is_superuser:
            count = items_crud.count_items(session=self.session)
            items = items_crud.list_items(session=self.session, skip=skip, limit=limit)
            return items, count

        count = items_crud.count_items_by_owner(
            session=self.session, owner_id=current_user.id
        )
        items = items_crud.list_items_by_owner(
            session=self.session, owner_id=current_user.id, skip=skip, limit=limit
        )
        return items, count

    def read_item(self, *, current_user: User, item_id: uuid.UUID) -> Item:
        item = self._get_item_or_raise(item_id)
        self._ensure_can_access(current_user=current_user, item=item)
        return item

    def create_item(self, *, current_user: User, item_in: ItemCreate) -> Item:
        return items_crud.create_item(
            session=self.session, item_in=item_in, owner_id=current_user.id
        )

    def update_item(
        self,
        *,
        current_user: User,
        item_id: uuid.UUID,
        item_in: ItemUpdate,
    ) -> Item:
        item = self._get_item_or_raise(item_id)
        self._ensure_can_access(current_user=current_user, item=item)
        return items_crud.update_item(
            session=self.session, db_item=item, item_in=item_in
        )

    def delete_item(self, *, current_user: User, item_id: uuid.UUID) -> None:
        item = self._get_item_or_raise(item_id)
        self._ensure_can_access(current_user=current_user, item=item)
        items_crud.delete_item(session=self.session, db_item=item)

    def _get_item_or_raise(self, item_id: uuid.UUID) -> Item:
        item = items_crud.get_item(session=self.session, item_id=item_id)
        if not item:
            raise ResourceNotFoundError("Item", item_id)
        return item

    @staticmethod
    def _ensure_can_access(*, current_user: User, item: Item) -> None:
        if not current_user.is_superuser and item.owner_id != current_user.id:
            raise PermissionDeniedError()
