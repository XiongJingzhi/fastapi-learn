from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class TodoBase(BaseModel):
    """待办事项基础模式"""
    title: str = Field(..., min_length=1, max_length=200, description="待办事项标题")
    description: Optional[str] = Field(None, description="待办事项描述")
    is_completed: Optional[bool] = Field(False, description="是否完成")


class TodoCreate(TodoBase):
    """创建待办事项模式"""
    pass


class TodoUpdate(BaseModel):
    """更新待办事项模式"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="待办事项标题")
    description: Optional[str] = Field(None, description="待办事项描述")
    is_completed: Optional[bool] = Field(None, description="是否完成")


class TodoInDBBase(TodoBase):
    """数据库中的待办事项基础模式"""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Todo(TodoInDBBase):
    """待办事项响应模式"""
    pass


class TodoWithTodo(TodoInDBBase):
    """带用户信息的待办事项模式（可选扩展）"""
    # 这里可以添加用户信息字段，如果需要在响应中包含用户信息
    pass