import uuid

from sqlmodel import Session

from app.core.config import settings
from app.core.exceptions import (
    AppException,
    BadRequestError,
    ConflictError,
    PermissionDeniedError,
)
from app.core.security import get_password_hash, verify_password
from app.crud import items as items_crud
from app.crud import users as users_crud
from app.models import (
    Message,
    UpdatePassword,
    User,
    UserCreate,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.services.email_events import publish_registration_email_event


class UserService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def read_users(self, *, skip: int, limit: int) -> UsersPublic:
        count = users_crud.count_users(session=self.session)
        users = users_crud.list_users(session=self.session, skip=skip, limit=limit)
        return UsersPublic(data=users, count=count)

    def create_user(self, *, user_in: UserCreate) -> User:
        user = users_crud.get_user_by_email(session=self.session, email=user_in.email)
        if user:
            raise BadRequestError(
                "The user with this email already exists in the system.",
                "USER_ALREADY_EXISTS",
            )
        user = users_crud.create_user(session=self.session, user_create=user_in)
        self._publish_registration_email(
            email_to=user_in.email,
            username=user_in.email,
            password=user_in.password,
        )
        return user

    def update_user_me(self, *, current_user: User, user_in: UserUpdateMe) -> User:
        if user_in.email:
            existing_user = users_crud.get_user_by_email(
                session=self.session, email=user_in.email
            )
            if existing_user and existing_user.id != current_user.id:
                raise ConflictError(
                    "User with this email already exists", "USER_EMAIL_CONFLICT"
                )
        user_data = user_in.model_dump(exclude_unset=True)
        current_user.sqlmodel_update(user_data)
        return users_crud.save_user(session=self.session, db_user=current_user)

    def update_password_me(self, *, current_user: User, body: UpdatePassword) -> Message:
        verified, _ = verify_password(
            body.current_password, current_user.hashed_password
        )
        if not verified:
            raise BadRequestError("Incorrect password", "INCORRECT_PASSWORD")
        if body.current_password == body.new_password:
            raise BadRequestError(
                "New password cannot be the same as the current one",
                "PASSWORD_UNCHANGED",
            )
        hashed_password = get_password_hash(body.new_password)
        current_user.hashed_password = hashed_password
        users_crud.save_user(session=self.session, db_user=current_user)
        return Message(message="Password updated successfully")

    @staticmethod
    def read_user_me(*, current_user: User) -> User:
        return current_user

    def delete_user_me(self, *, current_user: User) -> Message:
        if current_user.is_superuser:
            raise PermissionDeniedError("Super users are not allowed to delete themselves")
        users_crud.delete_user(session=self.session, db_user=current_user)
        return Message(message="User deleted successfully")

    def register_user(self, *, user_in: UserRegister) -> User:
        user = users_crud.get_user_by_email(session=self.session, email=user_in.email)
        if user:
            raise BadRequestError(
                "The user with this email already exists in the system",
                "USER_ALREADY_EXISTS",
            )
        user_create = UserCreate.model_validate(user_in)
        user = users_crud.create_user(session=self.session, user_create=user_create)
        self._publish_registration_email(
            email_to=user_in.email,
            username=user_in.email,
            password=user_in.password,
        )
        return user

    def _publish_registration_email(
        self, *, email_to: str, username: str, password: str
    ) -> None:
        if not settings.emails_enabled or not email_to:
            return
        publish_registration_email_event(
            email_to=email_to,
            username=username,
            password=password,
        )

    def read_user_by_id(self, *, user_id: uuid.UUID, current_user: User) -> User:
        user = users_crud.get_user(session=self.session, user_id=user_id)
        if user == current_user:
            return user
        if not current_user.is_superuser:
            raise PermissionDeniedError("The user doesn't have enough privileges")
        if user is None:
            raise AppException(
                status_code=404,
                detail="User not found",
                error_code="USER_NOT_FOUND",
            )
        return user

    def update_user(self, *, user_id: uuid.UUID, user_in: UserUpdate) -> User:
        db_user = users_crud.get_user(session=self.session, user_id=user_id)
        if not db_user:
            raise AppException(
                status_code=404,
                detail="The user with this id does not exist in the system",
                error_code="USER_NOT_FOUND",
            )
        if user_in.email:
            existing_user = users_crud.get_user_by_email(
                session=self.session, email=user_in.email
            )
            if existing_user and existing_user.id != user_id:
                raise ConflictError(
                    "User with this email already exists", "USER_EMAIL_CONFLICT"
                )
        return users_crud.update_user(
            session=self.session, db_user=db_user, user_in=user_in
        )

    def delete_user(self, *, user_id: uuid.UUID, current_user: User) -> Message:
        user = users_crud.get_user(session=self.session, user_id=user_id)
        if not user:
            raise AppException(
                status_code=404,
                detail="User not found",
                error_code="USER_NOT_FOUND",
            )
        if user == current_user:
            raise PermissionDeniedError("Super users are not allowed to delete themselves")
        items_crud.delete_items_by_owner(session=self.session, owner_id=user_id)
        users_crud.delete_user(session=self.session, db_user=user)
        return Message(message="User deleted successfully")
