import json

from pydantic import BaseModel, EmailStr, ValidationError

class User(BaseModel):
    id: int
    name: str
    email: EmailStr


if __name__ == "__main__":
    try:
        # 故意缺少 email，演示如何捕获 Pydantic 校验错误
        user = User(id=1, name="John Doe")
    except ValidationError as exc:
        print("Validation failed:")
        print(exc)
        print(exc.errors())
        # Pydantic v2: 使用 json.dumps 格式化错误信息
        print(json.dumps(exc.errors(), indent=2, ensure_ascii=False))

    # 成功示例
    user_ok = User(id=2, name="Jane Doe", email="jane@example.com")
    print("Validation succeeded:", user_ok.model_dump())
