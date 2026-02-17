from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="User Service")

# 模拟数据库
users_db = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
    2: {"id": 2, "name": "Bob", "email": "bob@example.com"},
    3: {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
}

class User(BaseModel):
    id: Optional[int] = None
    name: str
    email: str

class UserCreate(BaseModel):
    name: str
    email: str

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "user-service"}

@app.get("/users", response_model=list[User])
def get_users():
    """获取所有用户"""
    return list(users_db.values())

@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    """获取单个用户"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@app.post("/users", response_model=User)
def create_user(user: UserCreate):
    """创建用户"""
    user_id = max(users_db.keys()) + 1
    new_user = User(id=user_id, **user.dict())
    users_db[user_id] = new_user
    return new_user

@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: UserCreate):
    """更新用户"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    users_db[user_id] = User(id=user_id, **user.dict())
    return users_db[user_id]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
