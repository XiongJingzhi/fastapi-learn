from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import AuthServiceDep
from app.models import Message, NewPassword, Token

router = APIRouter()


@router.post("/login/access-token")
def login_access_token(
    auth_service: AuthServiceDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """OAuth2 compatible token login."""
    return auth_service.login_access_token(
        username=form_data.username,
        password=form_data.password,
    )


@router.post("/password-recovery/{email}")
def recover_password(email: str, auth_service: AuthServiceDep) -> Message:
    """Password recovery."""
    return auth_service.recover_password(email=email)


@router.post("/reset-password/")
def reset_password(auth_service: AuthServiceDep, body: NewPassword) -> Message:
    """Reset password."""
    return auth_service.reset_password(body=body)
