from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Todo(Base):
    """待办事项模型"""

    __tablename__ = "todos"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 待办事项内容
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 状态
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    # 外键 - 所属用户
    owner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # 关系 - 一个待办事项只属于一个用户
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="todos"
    )

    def __repr__(self) -> str:
        return f"<Todo(id={self.id}, title='{self.title}', completed={self.is_completed})>"