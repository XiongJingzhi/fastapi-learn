from datetime import datetime
from typing import Literal

from sqlmodel import SQLModel


class ExternalTodo(SQLModel):
    userId: int
    id: int
    title: str
    completed: bool


class ExternalTodoPublic(SQLModel):
    source: Literal["cache", "external"]
    cached_at: datetime | None = None
    data: ExternalTodo


class RedisHealthPublic(SQLModel):
    enabled: bool
    connected: bool


class SchedulerStatusPublic(SQLModel):
    enabled: bool
    running: bool
    jobs: list[str]
