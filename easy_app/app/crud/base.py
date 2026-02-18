from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

# 定义泛型类型变量
ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """基础 CRUD 操作类"""

    def __init__(self, model: Type[ModelType]):
        """
        CRUD 对象使用默认的增删改查方法

        Args:
            model: SQLAlchemy 模型类
        """
        self.model = model

    async def get(
        self, db: AsyncSession, id: Any
    ) -> Optional[ModelType]:
        """
        通过 ID 获取单个记录

        Args:
            db: 数据库会话
            id: 记录 ID

        Returns:
            模型实例或 None
        """
        statement = select(self.model).where(self.model.id == id)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        获取多个记录，支持分页

        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            模型实例列表
        """
        statement = select(self.model).offset(skip).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all()

    async def create(
        self, db: AsyncSession, *, obj_in: CreateSchemaType
    ) -> ModelType:
        """
        创建新记录

        Args:
            db: 数据库会话
            obj_in: 创建对象的 Pydantic 模式

        Returns:
            创建的模型实例
        """
        obj_in_data = obj_in.dict()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        更新记录

        Args:
            db: 数据库会话
            db_obj: 要更新的数据库对象
            obj_in: 更新的数据（Pydantic 模式或字典）

        Returns:
            更新后的模型实例
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(
        self, db: AsyncSession, *, id: int
    ) -> Optional[ModelType]:
        """
        删除记录

        Args:
            db: 数据库会话
            id: 要删除的记录 ID

        Returns:
            被删除的模型实例或 None
        """
        obj = await self.get(db, id=id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

    async def get_by_field(
        self, db: AsyncSession, *, field_name: str, field_value: Any
    ) -> Optional[ModelType]:
        """
        通过指定字段获取记录

        Args:
            db: 数据库会话
            field_name: 字段名
            field_value: 字段值

        Returns:
            模型实例或 None
        """
        statement = select(self.model).where(getattr(self.model, field_name) == field_value)
        result = await db.execute(statement)
        return result.scalar_one_or_none()