from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="Product Service")

# 模拟数据库
products_db = {
    1: {"id": 1, "name": "Laptop", "price": 999.99, "stock": 10},
    2: {"id": 2, "name": "Mouse", "price": 29.99, "stock": 50},
    3: {"id": 3, "name": "Keyboard", "price": 79.99, "stock": 30},
}

class Product(BaseModel):
    id: Optional[int] = None
    name: str
    price: float
    stock: int

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "product-service"}

@app.get("/products", response_model=list[Product])
def get_products():
    """获取所有产品"""
    return list(products_db.values())

@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    """获取单个产品"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    return products_db[product_id]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
