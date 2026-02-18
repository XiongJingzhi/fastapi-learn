from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """用户基础模式"""
    email: EmailStr = Field(..., description="用户邮箱")
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    is_active: Optional[bool] = Field(True, description="用户是否激活")


class UserCreate(UserBase):
    """创建用户模式"""
    password: str = Field(..., min_length=6, max_length=128, description="用户密码")


class UserUpdate(BaseModel):
    """更新用户模式"""
    email: Optional[EmailStr] = Field(None, description="用户邮箱")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    password: Optional[str] = Field(None, min_length=6, max_length=128, description="新密码")
    is_active: Optional[bool] = Field(None, description="用户是否激活")


class UserInDBBase(UserBase):
    """数据库中的用户基础模式"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class User(UserInDBBase):
    """用户响应模式"""
    pass


class UserInDB(UserInDBBase):
    """数据库中的用户模式（包含敏感信息）"""
    hashed_password: str