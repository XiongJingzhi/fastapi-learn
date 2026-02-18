from app.crud.base import CRUDBase
from app.crud.todo import todo_crud
from app.crud.user import user_crud

# 导出所有 CRUD 类和实例
__all__ = ["CRUDBase", "user_crud", "todo_crud"]