from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import uvicorn

app = FastAPI(title="API Gateway")

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 服务地址
services = {
    "users": "http://user-service:8000",
    "orders": "http://order-service:8000",
    "products": "http://product-service:8000",
}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "api-gateway"}

@app.api_route("/api/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_request(service: str, path: str, request: Request):
    """代理请求到后端服务"""
    if service not in services:
        raise HTTPException(status_code=404, detail="Service not found")

    service_url = services[service]
    url = f"{service_url}/{path}"

    # 转发请求
    body = await request.body()
    headers = dict(request.headers)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                timeout=30.0
            )
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
