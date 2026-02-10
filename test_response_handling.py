#!/usr/bin/env python3
"""
测试脚本：演示如何测试 FastAPI 响应处理示例

运行方式：
    # 先启动服务器
    python3 -m uvicorn app.examples.02_response_handling:app --reload

    # 然后在另一个终端运行此测试脚本
    python3 test_response_handling.py
"""

import asyncio
import httpx


BASE_URL = "http://localhost:8000"


async def test_user_endpoints():
    """测试用户相关接口"""
    print("\n" + "="*50)
    print("测试用户接口")
    print("="*50)

    async with httpx.AsyncClient() as client:
        # 1. 创建用户
        print("\n1. 创建用户")
        response = await client.post(
            f"{BASE_URL}/api/users/",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")

        user_id = response.json()["id"]

        # 2. 获取用户信息
        print("\n2. 获取用户信息")
        response = await client.get(f"{BASE_URL}/api/users/{user_id}")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")

        # 3. 获取用户列表
        print("\n3. 获取用户列表")
        response = await client.get(f"{BASE_URL}/api/users/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")


async def test_status_codes():
    """测试状态码"""
    print("\n" + "="*50)
    print("测试状态码")
    print("="*50)

    async with httpx.AsyncClient() as client:
        # 1. 200 OK
        print("\n1. 200 OK")
        response = await client.get(f"{BASE_URL}/api/status/ok")
        print(f"状态码: {response.status_code}")

        # 2. 201 Created
        print("\n2. 201 Created")
        response = await client.post(f"{BASE_URL}/api/status/created")
        print(f"状态码: {response.status_code}")

        # 3. 404 Not Found
        print("\n3. 404 Not Found")
        response = await client.get(f"{BASE_URL}/api/error/not-found")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")

        # 4. 422 Validation Error
        print("\n4. 自定义错误")
        response = await client.get(f"{BASE_URL}/api/error/custom")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")


async def test_headers():
    """测试响应头"""
    print("\n" + "="*50)
    print("测试响应头")
    print("="*50)

    async with httpx.AsyncClient() as client:
        print("\n1. 自定义响应头")
        response = await client.get(f"{BASE_URL}/api/headers/custom")
        print(f"状态码: {response.status_code}")
        print(f"自定义头: {dict(response.headers)}")

        print("\n2. CORS 头")
        response = await client.get(f"{BASE_URL}/api/headers/cors")
        print(f"CORS 头: {response.headers.get('Access-Control-Allow-Origin')}")


async def test_streaming():
    """测试流式响应"""
    print("\n" + "="*50)
    print("测试流式响应")
    print("="*50)

    async with httpx.AsyncClient() as client:
        print("\n1. 流式数据（前 5 行）")
        async with client.stream("GET", f"{BASE_URL}/api/stream/data") as response:
            print(f"状态码: {response.status_code}")
            print("内容:")
            count = 0
            async for chunk in response.aiter_bytes():
                print(chunk.decode("utf-8"), end="")
                count += 1
                if count >= 5:
                    print("\n... (省略后续内容)")
                    break


async def test_redirect():
    """测试重定向"""
    print("\n" + "="*50)
    print("测试重定向")
    print("="*50)

    async with httpx.AsyncClient(follow_redirects=False) as client:
        print("\n1. 临时重定向 (307)")
        response = await client.get(f"{BASE_URL}/api/redirect/old-url")
        print(f"状态码: {response.status_code}")
        print(f"重定向到: {response.headers.get('location')}")


async def main():
    """主测试函数"""
    print("\n" + "="*50)
    print("FastAPI 响应处理示例测试")
    print("="*50)

    try:
        # 测试根路径
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/")
            if response.status_code == 200:
                print("\n✓ 服务器连接成功")
                print(f"API 信息: {response.json()}")
            else:
                print("\n✗ 服务器未响应，请先启动 uvicorn")
                return

        # 运行所有测试
        await test_user_endpoints()
        await test_status_codes()
        await test_headers()
        await test_streaming()
        await test_redirect()

        print("\n" + "="*50)
        print("所有测试完成!")
        print("="*50)

    except httpx.ConnectError:
        print("\n✗ 无法连接到服务器")
        print("请先运行: python3 -m uvicorn app.examples.02_response_handling:app --reload")
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")


if __name__ == "__main__":
    asyncio.run(main())
