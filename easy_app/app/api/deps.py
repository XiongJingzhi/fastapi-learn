from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_token
from app.crud.user import user_crud
from app.database import get_db
from app.models.user import User

# OAuth2 密码流
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_str}/auth/login"
)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    获取当前认证用户

    Args:
        db: 数据库会话
        token: JWT 访问令牌

    Returns:
        当前认证用户

    Raises:
        HTTPException: 认证失败时抛出 401 错误
    """
    # 验证令牌
    token_data = verify_token(token)
    if token_data is None or token_data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 获取用户
    user = await user_crud.get(db, id=token_data.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前激活用户

    Args:
        current_user: 当前认证用户

    Returns:
        当前激活用户

    Raises:
        HTTPException: 用户未激活时抛出 400 错误
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user