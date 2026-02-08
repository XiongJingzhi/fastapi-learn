"""
阶段 0.4: 阻塞陷阱 - 学会识别和避免阻塞操作

学习目标：
1. 理解什么是阻塞操作
2. 学会识别哪些代码会阻塞事件循环
3. 学会使用 run_in_executor() 在线程池中执行阻塞操作
4. 理解阻塞操作对性能的影响

⚠️  这是异步编程中最容易犯的错误！

常见阻塞操作：
- time.sleep() → 使用 asyncio.sleep()
- 同步的文件读写 → 使用 aiofiles
- 同步的HTTP请求 → 使用 httpx 或 aiohttp
- 同步的数据库操作 → 使用 asyncpg/aiomysql/SQLAlchemy async
- CPU密集型计算 → 使用 ProcessPoolExecutor

运行这个示例，观察阻塞操作如何影响性能！
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor


# ============ 阻塞 vs 非阻塞对比 ============

async def blocking_sleep(seconds: int):
    """❌ 阻塞版本：会阻塞整个事件循环"""
    print(f"  🔴 阻塞 sleep {seconds} 秒...")
    time.sleep(seconds)  # 这会阻塞整个事件循环！
    print(f"  ✅ 阻塞 sleep 完成")
    return f"阻塞{seconds}秒"


async def non_blocking_sleep(seconds: int):
    """✅ 非阻塞版本：不会阻塞事件循环"""
    print(f"  🟢 非阻塞 sleep {seconds} 秒...")
    await asyncio.sleep(seconds)  # 这不会阻塞事件循环
    print(f"  ✅ 非阻塞 sleep 完成")
    return f"非阻塞{seconds}秒"


async def blocking_example():
    """演示阻塞操作的问题"""
    print("\n📌 演示1: 使用 time.sleep() 的阻塞版本")
    print("-" * 50)

    start = time.time()

    # 虽然用了 async/await，但 time.sleep() 会阻塞整个事件循环
    results = await asyncio.gather(
        blocking_sleep(2),
        blocking_sleep(2),
        blocking_sleep(2),
    )

    elapsed = time.time() - start
    print(f"\n⏱️  总耗时: {elapsed:.2f} 秒")
    print(f"❌ 问题：虽然是异步代码，但因为阻塞操作，任务是顺序执行的！")
    print(f"❌ 总时间 = 2+2+2 = 6秒，而不是并发的2秒")


async def non_blocking_example():
    """演示正确的异步操作"""
    print("\n📌 演示2: 使用 asyncio.sleep() 的非阻塞版本")
    print("-" * 50)

    start = time.time()

    # 正确的异步操作，不会阻塞
    results = await asyncio.gather(
        non_blocking_sleep(2),
        non_blocking_sleep(2),
        non_blocking_sleep(2),
    )

    elapsed = time.time() - start
    print(f"\n⏱️  总耗时: {elapsed:.2f} 秒")
    print(f"✅ 任务真正并发执行，总时间约等于单个任务时间")


# ============ 处理阻塞操作的正确方式 ============

def blocking_cpu_work(n: int) -> int:
    """模拟CPU密集型计算（阻塞操作）"""
    print(f"  🔴 CPU计算: 计算 {n} 的阶乘...")
    result = 1
    for i in range(1, n + 1):
        result *= i
    print(f"  ✅ CPU计算完成: {n}! = {result}")
    return result


async def run_in_thread_pool(func, *args):
    """在线程池中运行阻塞函数"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)


async def cpu_bound_example():
    """演示如何处理CPU密集型任务"""
    print("\n📌 演示3: 处理CPU密集型任务（使用线程池）")
    print("-" * 50)

    start = time.time()

    # 使用 ThreadPoolExecutor 在线程池中运行阻塞的CPU任务
    with ThreadPoolExecutor(max_workers=3) as executor:
        loop = asyncio.get_event_loop()

        results = await asyncio.gather(
            loop.run_in_executor(executor, blocking_cpu_work, 1000),
            loop.run_in_executor(executor, blocking_cpu_work, 1000),
            loop.run_in_executor(executor, blocking_cpu_work, 1000),
        )

    elapsed = time.time() - start
    print(f"\n⏱️  总耗时: {elapsed:.2f} 秒")
    print(f"✅ 使用线程池，CPU任务并发执行")


# ============ 常见阻塞操作对照表 ============

def print_blocking_reference():
    """打印常见阻塞操作的正确替代方案"""
    print("\n📌 常见阻塞操作对照表")
    print("-" * 50)

    reference = """
    ❌ 阻塞操作                    →  ✅ 异步替代方案
    ════════════════════════════════════════════════════════

    time.sleep(1)                →  await asyncio.sleep(1)

    time.sleep()                 →  await asyncio.sleep()

    with open('file.txt')        →  import aiofiles
    f.read()                     →     async with aiofiles.open('file.txt') as f
                                  →         content = await f.read()

    requests.get('url')          →  import httpx
                                  →  async with httpx.AsyncClient() as client:
                                  →      response = await client.get('url')

    urllib.request.urlopen()     →  import httpx
                                  →  async with httpx.AsyncClient() as client:
                                  →      response = await client.get('url')

    同步数据库操作                →  使用异步驱动:
    (sqlite3/pymysql)            →  - asyncpg (PostgreSQL)
                                  →  - aiomysql (MySQL)
                                  →  - motor (MongoDB)

    CPU密集型计算                 →  loop.run_in_executor(
    (在主线程)                    →      ThreadPoolExecutor(),
                                  →      cpu_bound_function
                                  →  )

    ════════════════════════════════════════════════════════
    """

    print(reference)


def main():
    """运行所有示例"""
    print("\n" + "="*50)
    print("🎓 阶段 0.4: 阻塞陷阱 - 异步编程的最大敌人")
    print("="*50)

    asyncio.run(blocking_example())
    asyncio.run(non_blocking_example())
    asyncio.run(cpu_bound_example())
    print_blocking_reference()

    print("\n" + "="*50)
    print("💡 核心要点：")
    print("1. 在异步代码中使用阻塞操作会阻塞整个事件循环")
    print("2. 常见的阻塞操作：time.sleep、同步IO、同步HTTP、CPU计算")
    print("3. 总是使用异步版本的库（aiofiles、httpx、asyncpg等）")
    print("4. 对于没有异步版本的阻塞操作，使用 run_in_executor()")
    print("5. CPU密集型任务应该用 ProcessPoolExecutor（进程池）")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
