from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
import httpx

app = FastAPI(title="Order Service")

# 服务地址
USER_SERVICE_URL = "http://user-service:8000"
PRODUCT_SERVICE_URL = "http://product-service:8000"

# 模拟数据库
orders_db = {}
order_id_counter = 1

class Order(BaseModel):
    id: Optional[int] = None
    user_id: int
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    user_id: int
    product_id: int
    quantity: int

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "order-service"}

@app.get("/orders")
def get_orders():
    """获取所有订单"""
    return list(orders_db.values())

@app.get("/orders/{order_id}")
def get_order(order_id: int):
    """获取单个订单"""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders_db[order_id]

@app.post("/orders")
async def create_order(order: OrderCreate):
    """创建订单（调用其他服务）"""
    global order_id_counter

    # 调用用户服务验证用户
    async with httpx.AsyncClient() as client:
        try:
            user_response = await client.get(f"{USER_SERVICE_URL}/users/{order.user_id}")
            if user_response.status_code == 404:
                raise HTTPException(status_code=400, detail="User not found")
            user = user_response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail="User service unavailable")

    # 调用产品服务获取产品信息
    async with httpx.AsyncClient() as client:
        try:
            product_response = await client.get(f"{PRODUCT_SERVICE_URL}/products/{order.product_id}")
            if product_response.status_code == 404:
                raise HTTPException(status_code=400, detail="Product not found")
            product = product_response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail="Product service unavailable")

    # 创建订单
    new_order = Order(
        id=order_id_counter,
        user_id=order.user_id,
        product_id=order.product_id,
        quantity=order.quantity
    )
    orders_db[order_id_counter] = new_order
    order_id_counter += 1

    # 返回订单详情（包含用户和产品信息）
    return {
        "order": new_order.dict(),
        "user": user,
        "product": product
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
