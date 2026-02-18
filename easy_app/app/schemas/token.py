from typing import Optional

from pydantic import BaseModel, Field


class Token(BaseModel):
    """JWT 令牌响应模式"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")


class TokenData(BaseModel):
    """JWT 令牌数据模式"""
    username: Optional[str] = Field(None, description="用户名")
    user_id: Optional[int] = Field(None, description="用户ID")


class TokenPayload(BaseModel):
    """JWT 令牌载荷模式"""
    sub: Optional[str] = None
    exp: Optional[int] = None
    type: Optional[str] = None