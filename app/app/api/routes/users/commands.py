import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, UserServiceDep, get_current_active_superuser
from app.models import (
    Message,
    UpdatePassword,
    UserCreate,
    UserPublic,
    UserRegister,
    UserUpdate,
    UserUpdateMe,
)

router = APIRouter()


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
def create_user(*, session: UserServiceDep, user_in: UserCreate) -> Any:
    """Create new user."""
    return session.create_user(user_in=user_in)


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: UserServiceDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """Update own user."""
    return session.update_user_me(current_user=current_user, user_in=user_in)


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: UserServiceDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """Update own password."""
    return session.update_password_me(current_user=current_user, body=body)


@router.delete("/me", response_model=Message)
def delete_user_me(session: UserServiceDep, current_user: CurrentUser) -> Any:
    """Delete own user."""
    return session.delete_user_me(current_user=current_user)


@router.post("/signup", response_model=UserPublic)
def register_user(session: UserServiceDep, user_in: UserRegister) -> Any:
    """Create new user without login."""
    return session.register_user(user_in=user_in)


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
def update_user(
    *,
    session: UserServiceDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> Any:
    """Update a user."""
    return session.update_user(user_id=user_id, user_in=user_in)


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
def delete_user(
    session: UserServiceDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """Delete a user."""
    return session.delete_user(user_id=user_id, current_user=current_user)
