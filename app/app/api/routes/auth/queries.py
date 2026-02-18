from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import AuthServiceDep, CurrentUser, get_current_active_superuser
from app.models import UserPublic

router = APIRouter()


@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> Any:
    """Test access token."""
    return current_user


@router.post(
    "/password-recovery-html-content/{email}",
    dependencies=[Depends(get_current_active_superuser)],
)
def recover_password_html_content(email: str, auth_service: AuthServiceDep) -> Any:
    """HTML content for password recovery."""
    return auth_service.recover_password_html_content(email=email)
