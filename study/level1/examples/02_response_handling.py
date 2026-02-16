"""
Level 1 - Example 02: 响应处理 (Response Handling)

本示例展示 FastAPI 的各种响应类型：
1. 基本 JSON 响应
2. 使用响应模型 (response_model)
3. 文件响应 (FileResponse)
4. 流式响应 (StreamingResponse)
5. 响应状态码

运行方式:
    uvicorn study.level1.examples.02_response_handling:app --reload
"""

from fastapi import FastAPI, status
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
import io

app = FastAPI(title="Level 1 - Response Handling")


# ========== 数据模型 ==========

class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None


class UserInDB(UserBase):
    """数据库中的完整用户信息"""
    id: int
    password_hash: str  # 敏感字段，不应返回给前端
    created_at: datetime


class UserResponse(UserBase):
    """返回给前端的安全用户信息"""
    id: int
    created_at: datetime
    # 注意：没有 password_hash 字段！


class ItemBase(BaseModel):
    """商品基础模型"""
    name: str
    description: Optional[str] = None
    price: float


class ItemInDB(ItemBase):
    """数据库中的商品"""
    id: int
    cost: float  # 成本价（敏感信息）
    in_stock: bool = True
    created_at: datetime


class ItemResponse(ItemBase):
    """返回给前端的商品（不包含成本价）"""
    id: int
    in_stock: bool
    created_at: datetime


# ========== 模拟数据库 ==========

fake_users_db: dict[int, UserInDB] = {
    1: UserInDB(
        id=1,
        username="alice",
        email="alice@example.com",
        full_name="Alice Johnson",
        password_hash="hashed_secret_123",
        created_at=datetime(2024, 1, 10, 8, 0, 0)
    ),
    2: UserInDB(
        id=2,
        username="bob",
        email="bob@example.com",
        full_name="Bob Smith",
        password_hash="hashed_secret_456",
        created_at=datetime(2024, 1, 11, 9, 30, 0)
    )
}

fake_items_db: dict[int, ItemInDB] = {
    1: ItemInDB(
        id=1,
        name="Laptop",
        description="High-performance laptop",
        price=999.99,
        cost=600.00,
        in_stock=True,
        created_at=datetime(2024, 1, 15, 10, 0, 0)
    ),
    2: ItemInDB(
        id=2,
        name="Mouse",
        description="Wireless mouse",
        price=29.99,
        cost=5.00,
        in_stock=True,
        created_at=datetime(2024, 1, 15, 11, 0, 0)
    ),
    3: ItemInDB(
        id=3,
        name="Keyboard",
        description="Mechanical keyboard",
        price=79.99,
        cost=20.00,
        in_stock=False,
        created_at=datetime(2024, 1, 15, 12, 0, 0)
    )
}


# ========== 1. 基本 JSON 响应 ==========

@app.get("/")
async def root():
    """最简单的 JSON 响应"""
    return {
        "message": "Welcome to Response Handling Demo",
        "version": "1.0.0",
        "endpoints": {
            "users": "/users/{user_id}",
            "items": "/items/{item_id}",
            "download": "/download/users",
            "stream": "/stream/numbers"
        }
    }


@app.get("/hello")
async def say_hello():
    """简单 JSON 响应"""
    return {"message": "Hello, World!"}


# ========== 2. 使用响应模型 ==========

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """
    获取用户信息 - 自动过滤敏感字段

    response_model 参数会自动过滤 UserInDB 中的 password_hash 字段
    """
    user = fake_users_db.get(user_id)

    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    # FastAPI 自动只返回 UserResponse 中定义的字段
    return user


@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    """
    获取商品信息 - 自动过滤成本价字段

    返回的 JSON 不包含 cost 字段
    """
    item = fake_items_db.get(item_id)

    if not item:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Item not found")

    # 自动过滤 cost 字段
    return item


# ========== 3. 文件响应 ==========

@app.get("/download/users")
async def download_users_csv():
    """
    返回 CSV 文件下载

    实际场景：导出数据、生成报告、返回用户上传的文件
    """
    # 生成 CSV 内容
    output = io.StringIO()

    # 写入表头
    output.write("id,username,email,full_name,created_at\n")

    # 写入数据
    for user in fake_users_db.values():
        created_at_str = user.created_at.strftime("%Y-%m-%d %H:%M:%S")
        output.write(f"{user.id},{user.username},{user.email},{user.full_name},{created_at_str}\n")

    # 生成文件名
    filename = f"users_{datetime.now().strftime('%Y%m%d')}.csv"

    # 返回 CSV 文件
    return StreamingResponse(
        content=iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@app.get("/download/sample-text")
async def download_sample_text():
    """返回文本文件"""
    content = """This is a sample text file.

You can download this file to test FileResponse.

Content:
- Line 1: Some text
- Line 2: More text
- Line 3: Even more text
"""

    from fastapi.responses import Response
    return Response(
        content=content,
        media_type="text/plain",
        headers={
            "Content-Disposition": "attachment; filename=sample.txt"
        }
    )


# ========== 4. 流式响应 ==========

async def generate_numbers():
    """生成数字流 - 模拟实时数据"""
    for i in range(1, 11):
        yield f"data: {i}\n\n"
        import asyncio
        await asyncio.sleep(0.5)  # 模拟延迟


@app.get("/stream/numbers")
async def stream_numbers():
    """
    流式返回数字 - SSE (Server-Sent Events) 格式

    实际场景：实时数据推送、聊天消息、股票行情
    """
    return StreamingResponse(
        content=generate_numbers(),
        media_type="text/event-stream"
    )


async def generate_large_file():
    """生成大文件内容 - 分块返回"""
    for i in range(100):
        yield f"Line {i}: Some content here...\n"


@app.get("/stream/large-file")
async def stream_large_file():
    """
    流式返回大文件

    优点：
    - 不占用大量内存
    - 客户端可以逐步接收处理
    - 适合大文件下载
    """
    return StreamingResponse(
        content=generate_large_file(),
        media_type="text/plain"
    )


# ========== 5. 响应状态码 ==========

@app.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserBase):
    """
    创建用户 - 返回 201 状态码

    201 Created: 成功创建资源
    """
    from fastapi import HTTPException

    # 检查用户名是否已存在
    for existing_user in fake_users_db.values():
        if existing_user.username == user.username:
            raise HTTPException(
                status_code=409,
                detail="Username already exists"
            )

    # 模拟创建用户
    new_user = UserInDB(
        id=len(fake_users_db) + 1,
        password_hash="new_hashed_password",
        **user.model_dump(),  # Pydantic v2 语法
        created_at=datetime.now()
    )

    fake_users_db[new_user.id] = new_user

    return new_user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    """
    删除用户 - 返回 204 状态码

    204 No Content: 成功删除，无返回内容
    """
    from fastapi import HTTPException

    if user_id not in fake_users_db:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    del fake_users_db[user_id]

    return None  # 204 状态码不返回内容


# ========== 6. 综合示例：完整响应处理 ==========

@app.get("/users/{user_id}/profile")
async def get_user_profile_with_response_model(
    user_id: int,
    format: str = "json"
):
    """
    综合示例：根据格式参数返回不同响应
    - format=json: 返回 JSON
    - format=csv: 返回 CSV 文件
    """
    from fastapi import HTTPException

    user = fake_users_db.get(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 根据格式返回不同响应
    if format == "csv":
        # 生成 CSV
        output = io.StringIO()
        output.write("id,username,email,full_name,created_at\n")
        output.write(f"{user.id},{user.username},{user.email},{user.full_name},{user.created_at}\n")

        filename = f"user_{user_id}_profile.csv"
        return StreamingResponse(
            content=iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    # 默认返回 JSON（自动过滤 password_hash）
    return user


# ========== 主程序入口 ==========

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("FastAPI Response Handling Demo")
    print("=" * 60)
    print()
    print("测试端点：")
    print("  基本 JSON:")
    print("    curl http://localhost:8000/")
    print("    curl http://localhost:8000/hello")
    print()
    print("  响应模型（自动过滤敏感字段）：")
    print("    curl http://localhost:8000/users/1")
    print("    curl http://localhost:8000/items/1")
    print()
    print("  文件下载：")
    print("    curl http://localhost:8000/download/users -o users.csv")
    print()
    print("  流式响应：")
    print("    curl -N http://localhost:8000/stream/numbers")
    print()
    print("  状态码：")
    print("    curl -X POST http://localhost:8000/users -H 'Content-Type: application/json' \\")
    print("      -d '{\"username\": \"charlie\", \"email\": \"charlie@example.com\"}'")
    print()
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
