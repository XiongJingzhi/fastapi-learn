from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.core.exceptions import AppException
from app.core.redis import get_redis_cache
from app.integrations.external_api import get_external_todo_client
from app.models import TokenPayload, User
from app.services.auth import AuthService
from app.services.external_api import ExternalApiService
from app.services.items import ItemService
from app.services.users import UserService

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise AppException(
            status_code=403,
            detail="Could not validate credentials",
            error_code="INVALID_CREDENTIALS",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise AppException(
            status_code=404,
            detail="User not found",
            error_code="USER_NOT_FOUND",
        )
    if not user.is_active:
        raise AppException(
            status_code=400,
            detail="Inactive user",
            error_code="USER_INACTIVE",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise AppException(
            status_code=403,
            detail="The user doesn't have enough privileges",
            error_code="PERMISSION_DENIED",
        )
    return current_user


def get_item_service(session: SessionDep) -> ItemService:
    return ItemService(session=session)


ItemServiceDep = Annotated[ItemService, Depends(get_item_service)]


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session=session)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_user_service(session: SessionDep) -> UserService:
    return UserService(session=session)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_external_api_service() -> ExternalApiService:
    return ExternalApiService(
        external_client=get_external_todo_client(),
        cache=get_redis_cache(),
    )


ExternalApiServiceDep = Annotated[ExternalApiService, Depends(get_external_api_service)]
