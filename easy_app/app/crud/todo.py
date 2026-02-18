from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.base import CRUDBase
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoUpdate


class CRUDTodo(CRUDBase[Todo, TodoCreate, TodoUpdate]):
    """待办事项 CRUD 操作类"""

    async def create_with_owner(
        self, db: AsyncSession, *, obj_in: TodoCreate, owner_id: int
    ) -> Todo:
        """
        为指定用户创建待办事项

        Args:
            db: 数据库会话
            obj_in: 创建待办事项的数据
            owner_id: 所有者用户 ID

        Returns:
            创建的待办事项实例
        """
        db_obj = Todo(
            title=obj_in.title,
            description=obj_in.description,
            is_completed=obj_in.is_completed,
            owner_id=owner_id,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_owner(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        skip: int = 0,
        limit: int = 100,
        completed: Optional[bool] = None
    ) -> List[Todo]:
        """
        获取指定用户的待办事项列表，支持分页和完成状态过滤

        Args:
            db: 数据库会话
            owner_id: 所有者用户 ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            completed: 按完成状态过滤，None 表示不过滤

        Returns:
            待办事项列表
        """
        statement = select(Todo).where(Todo.owner_id == owner_id)

        # 添加完成状态过滤
        if completed is not None:
            statement = statement.where(Todo.is_completed == completed)

        # 添加分页
        statement = statement.offset(skip).limit(limit).order_by(Todo.created_at.desc())

        result = await db.execute(statement)
        return result.scalars().all()

    async def get_completed_count(
        self, db: AsyncSession, *, owner_id: int
    ) -> int:
        """
        获取用户已完成的待办事项数量

        Args:
            db: 数据库会话
            owner_id: 所有者用户 ID

        Returns:
            已完成待办事项数量
        """
        from sqlalchemy import func

        statement = (
            select(func.count(Todo.id))
            .where(Todo.owner_id == owner_id)
            .where(Todo.is_completed == True)
        )
        result = await db.execute(statement)
        return result.scalar()

    async def get_pending_count(
        self, db: AsyncSession, *, owner_id: int
    ) -> int:
        """
        获取用户未完成的待办事项数量

        Args:
            db: 数据库会话
            owner_id: 所有者用户 ID

        Returns:
            未完成待办事项数量
        """
        from sqlalchemy import func

        statement = (
            select(func.count(Todo.id))
            .where(Todo.owner_id == owner_id)
            .where(Todo.is_completed == False)
        )
        result = await db.execute(statement)
        return result.scalar()

    async def mark_as_completed(
        self, db: AsyncSession, *, todo_id: int, owner_id: int
    ) -> Optional[Todo]:
        """
        标记待办事项为已完成

        Args:
            db: 数据库会话
            todo_id: 待办事项 ID
            owner_id: 所有者用户 ID

        Returns:
            更新后的待办事项实例或 None
        """
        todo = await self.get(db, id=todo_id)
        if todo and todo.owner_id == owner_id:
            todo.is_completed = True
            await db.commit()
            await db.refresh(todo)
            return todo
        return None

    async def mark_as_pending(
        self, db: AsyncSession, *, todo_id: int, owner_id: int
    ) -> Optional[Todo]:
        """
        标记待办事项为未完成

        Args:
            db: 数据库会话
            todo_id: 待办事项 ID
            owner_id: 所有者用户 ID

        Returns:
            更新后的待办事项实例或 None
        """
        todo = await self.get(db, id=todo_id)
        if todo and todo.owner_id == owner_id:
            todo.is_completed = False
            await db.commit()
            await db.refresh(todo)
            return todo
        return None

    async def remove_by_owner(
        self, db: AsyncSession, *, todo_id: int, owner_id: int
    ) -> Optional[Todo]:
        """
        删除用户的待办事项

        Args:
            db: 数据库会话
            todo_id: 待办事项 ID
            owner_id: 所有者用户 ID

        Returns:
            被删除的待办事项实例或 None
        """
        todo = await self.get(db, id=todo_id)
        if todo and todo.owner_id == owner_id:
            await db.delete(todo)
            await db.commit()
            return todo
        return None


# 创建待办事项 CRUD 实例
todo_crud = CRUDTodo(Todo)