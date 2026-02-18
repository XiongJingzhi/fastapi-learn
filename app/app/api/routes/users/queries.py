import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, UserServiceDep, get_current_active_superuser
from app.models import UserPublic, UsersPublic

router = APIRouter()


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def read_users(session: UserServiceDep, skip: int = 0, limit: int = 100) -> Any:
    """Retrieve users."""
    return session.read_users(skip=skip, limit=limit)


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser, session: UserServiceDep) -> Any:
    """Get current user."""
    return session.read_user_me(current_user=current_user)


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: uuid.UUID, session: UserServiceDep, current_user: CurrentUser
) -> Any:
    """Get user by id."""
    return session.read_user_by_id(user_id=user_id, current_user=current_user)
