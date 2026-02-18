from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.crud.todo import todo_crud
from app.database import get_db
from app.models.user import User
from app.schemas.todo import Todo, TodoCreate, TodoUpdate

router = APIRouter()


@router.post("/", response_model=Todo)
async def create_todo(
    *,
    db: AsyncSession = Depends(get_db),
    todo_in: TodoCreate,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    创建新的待办事项
    """
    todo = await todo_crud.create_with_owner(
        db, obj_in=todo_in, owner_id=current_user.id
    )
    return todo


@router.get("/", response_model=List[Todo])
async def read_todos(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    completed: Optional[bool] = Query(None, description="按完成状态过滤"),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    获取当前用户的待办事项列表
    """
    todos = await todo_crud.get_by_owner(
        db,
        owner_id=current_user.id,
        skip=skip,
        limit=limit,
        completed=completed
    )
    return todos


@router.get("/stats", response_model=dict)
async def get_todo_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    获取待办事项统计信息
    """
    completed_count = await todo_crud.get_completed_count(db, owner_id=current_user.id)
    pending_count = await todo_crud.get_pending_count(db, owner_id=current_user.id)

    return {
        "completed": completed_count,
        "pending": pending_count,
        "total": completed_count + pending_count
    }


@router.get("/{todo_id}", response_model=Todo)
async def read_todo(
    todo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    获取特定的待办事项
    """
    todo = await todo_crud.get(db, id=todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )

    # 检查是否是待办事项的所有者
    if todo.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return todo


@router.put("/{todo_id}", response_model=Todo)
async def update_todo(
    *,
    db: AsyncSession = Depends(get_db),
    todo_id: int,
    todo_in: TodoUpdate,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    更新待办事项
    """
    todo = await todo_crud.get(db, id=todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )

    # 检查是否是待办事项的所有者
    if todo.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    todo = await todo_crud.update(db, db_obj=todo, obj_in=todo_in)
    return todo


@router.patch("/{todo_id}/complete", response_model=Todo)
async def mark_todo_completed(
    todo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    标记待办事项为已完成
    """
    todo = await todo_crud.mark_as_completed(
        db, todo_id=todo_id, owner_id=current_user.id
    )
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    return todo


@router.patch("/{todo_id}/pending", response_model=Todo)
async def mark_todo_pending(
    todo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    标记待办事项为未完成
    """
    todo = await todo_crud.mark_as_pending(
        db, todo_id=todo_id, owner_id=current_user.id
    )
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    return todo


@router.delete("/{todo_id}", response_model=Todo)
async def delete_todo(
    todo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    删除待办事项
    """
    todo = await todo_crud.remove_by_owner(
        db, todo_id=todo_id, owner_id=current_user.id
    )
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    return todo