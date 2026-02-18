from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """用户 CRUD 操作类"""

    async def get_by_email(
        self, db: AsyncSession, *, email: str
    ) -> Optional[User]:
        """
        通过邮箱获取用户

        Args:
            db: 数据库会话
            email: 用户邮箱

        Returns:
            用户实例或 None
        """
        statement = select(User).where(User.email == email)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_username(
        self, db: AsyncSession, *, username: str
    ) -> Optional[User]:
        """
        通过用户名获取用户

        Args:
            db: 数据库会话
            username: 用户名

        Returns:
            用户实例或 None
        """
        statement = select(User).where(User.username == username)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def create(
        self, db: AsyncSession, *, obj_in: UserCreate
    ) -> User:
        """
        创建新用户（包含密码哈希）

        Args:
            db: 数据库会话
            obj_in: 创建用户的数据

        Returns:
            创建的用户实例
        """
        from app.core.security import get_password_hash

        # 创建用户数据字典
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password),
            is_active=obj_in.is_active,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: User,
        obj_in: UserUpdate
    ) -> User:
        """
        更新用户信息（如果更新密码则进行哈希）

        Args:
            db: 数据库会话
            db_obj: 要更新的用户对象
            obj_in: 更新的数据

        Returns:
            更新后的用户实例
        """
        from app.core.security import get_password_hash

        update_data = obj_in.dict(exclude_unset=True)

        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password

        return await super().update(db, db_obj=db_obj, obj_in=update_data)

    async def authenticate(
        self, db: AsyncSession, *, email: str, password: str
    ) -> Optional[User]:
        """
        验证用户身份

        Args:
            db: 数据库会话
            email: 用户邮箱
            password: 用户密码

        Returns:
            验证成功返回用户实例，否则返回 None
        """
        from app.core.security import verify_password

        user = await self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def is_active(self, user: User) -> bool:
        """
        检查用户是否激活

        Args:
            user: 用户实例

        Returns:
            用户是否激活
        """
        return user.is_active


# 创建用户 CRUD 实例
user_crud = CRUDUser(User)