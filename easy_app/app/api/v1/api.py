from fastapi import APIRouter

from app.api.v1.endpoints import auth, todos, users

api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(todos.router, prefix="/todos", tags=["待办事项"])