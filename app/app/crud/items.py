import uuid

from sqlmodel import Session, col, delete, func, select

from app.models import Item, ItemCreate, ItemUpdate


def count_items(*, session: Session) -> int:
    statement = select(func.count()).select_from(Item)
    return session.exec(statement).one()


def count_items_by_owner(*, session: Session, owner_id: uuid.UUID) -> int:
    statement = select(func.count()).select_from(Item).where(Item.owner_id == owner_id)
    return session.exec(statement).one()


def list_items(*, session: Session, skip: int, limit: int) -> list[Item]:
    statement = (
        select(Item).order_by(col(Item.created_at).desc()).offset(skip).limit(limit)
    )
    return list(session.exec(statement).all())


def list_items_by_owner(
    *, session: Session, owner_id: uuid.UUID, skip: int, limit: int
) -> list[Item]:
    statement = (
        select(Item)
        .where(Item.owner_id == owner_id)
        .order_by(col(Item.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_item(*, session: Session, item_id: uuid.UUID) -> Item | None:
    return session.get(Item, item_id)


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


def update_item(*, session: Session, db_item: Item, item_in: ItemUpdate) -> Item:
    update_dict = item_in.model_dump(exclude_unset=True)
    db_item.sqlmodel_update(update_dict)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


def delete_item(*, session: Session, db_item: Item) -> None:
    session.delete(db_item)
    session.commit()


def delete_items_by_owner(*, session: Session, owner_id: uuid.UUID) -> None:
    statement = delete(Item).where(col(Item.owner_id) == owner_id)
    session.exec(statement)  # type: ignore
