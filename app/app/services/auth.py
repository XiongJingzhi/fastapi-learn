from datetime import timedelta

from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.core.email import generate_reset_password_email
from app.core.exceptions import AppException, BadRequestError
from app.core.tokens import generate_password_reset_token, verify_password_reset_token
from app.crud import users as users_crud
from app.models import Message, NewPassword, Token, UserUpdate
from app.services.email_events import publish_password_reset_email_event


class AuthService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def login_access_token(self, *, username: str, password: str) -> Token:
        user = users_crud.authenticate(
            session=self.session, email=username, password=password
        )
        if not user:
            raise BadRequestError("Incorrect email or password", "INVALID_CREDENTIALS")
        if not user.is_active:
            raise BadRequestError("Inactive user", "USER_INACTIVE")
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return Token(
            access_token=security.create_access_token(
                user.id, expires_delta=access_token_expires
            )
        )

    def recover_password(self, *, email: str) -> Message:
        user = users_crud.get_user_by_email(session=self.session, email=email)
        if user and settings.emails_enabled:
            password_reset_token = generate_password_reset_token(email=email)
            publish_password_reset_email_event(
                email_to=user.email,
                email=email,
                token=password_reset_token,
            )
        return Message(
            message="If that email is registered, we sent a password recovery link"
        )

    def reset_password(self, *, body: NewPassword) -> Message:
        email = verify_password_reset_token(token=body.token)
        if not email:
            raise BadRequestError("Invalid token", "INVALID_TOKEN")
        user = users_crud.get_user_by_email(session=self.session, email=email)
        if not user:
            raise BadRequestError("Invalid token", "INVALID_TOKEN")
        if not user.is_active:
            raise BadRequestError("Inactive user", "USER_INACTIVE")
        user_in_update = UserUpdate(password=body.new_password)
        users_crud.update_user(
            session=self.session,
            db_user=user,
            user_in=user_in_update,
        )
        return Message(message="Password updated successfully")

    def recover_password_html_content(self, *, email: str) -> HTMLResponse:
        user = users_crud.get_user_by_email(session=self.session, email=email)
        if not user:
            raise AppException(
                status_code=404,
                detail="The user with this username does not exist in the system.",
                error_code="USER_NOT_FOUND",
            )
        password_reset_token = generate_password_reset_token(email=email)
        email_data = generate_reset_password_email(
            email_to=user.email, email=email, token=password_reset_token
        )
        return HTMLResponse(
            content=email_data.html_content, headers={"subject:": email_data.subject}
        )
