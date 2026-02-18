from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.schemas.token import TokenData

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建访问令牌

    Args:
        data: 要编码的数据
        expires_delta: 令牌过期时间差，默认使用配置中的过期时间

    Returns:
        JWT 令牌字符串
    """
    to_encode = data.copy()

    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire, "type": "access"})

    # 创建 JWT
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """
    验证 JWT 令牌并提取数据

    Args:
        token: JWT 令牌字符串

    Returns:
        令牌数据或 None（如果验证失败）
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        # 获取用户ID
        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        # 验证令牌类型
        token_type = payload.get("type")
        if token_type != "access":
            return None

        # 创建 TokenData 对象
        token_data = TokenData(
            user_id=int(user_id),
            username=payload.get("username")
        )
        return token_data

    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        密码是否正确
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    生成密码哈希

    Args:
        password: 明文密码

    Returns:
        哈希密码
    """
    return pwd_context.hash(password)