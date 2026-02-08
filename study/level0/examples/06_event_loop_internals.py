"""
架构师深度讲解：事件循环底层机制 - 可视化演示

这个脚本通过可视化方式展示：
1. 线程 vs 协程的内存消耗对比
2. 阻塞 IO vs 非阻塞 IO 的性能差异
3. 事件循环的工作流程
4. 协程调度的实际过程

运行：python -m study.level0.examples.06_under_the_hood
"""

import asyncio
import sys
import time
import threading
import tracemalloc
from typing import List, Any


# ============ 第一部分：内存消耗对比 ============

def measure_memory_threads(n: int) -> int:
    """测量 n 个线程的内存消耗"""
    tracemalloc.start()

    threads = []
    for i in range(n):
        t = threading.Thread(target=lambda: time.sleep(1))
        t.start()
        threads.append(t)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    for t in threads:
        t.join()

    return peak


async def measure_memory_coroutines(n: int) -> int:
    """测量 n 个协程的内存消耗"""
    tracemalloc.start()

    async def dummy_coro():
        await asyncio.sleep(1)

    coroutines = [dummy_coro() for _ in range(n)]
    await asyncio.gather(*coroutines)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return peak


def demo_memory_comparison():
    """演示：线程 vs 协程的内存消耗"""
    print("\n" + "="*60)
    print("📊 第一部分：内存消耗对比")
    print("="*60)

    n = 1000

    print(f"\n创建 {n} 个线程...")
    start = time.time()
    thread_memory = measure_memory_threads(n)
    thread_time = time.time() - start
    print(f"  ⏱️  耗时: {thread_time:.2f} 秒")
    print(f"  💾 内存峰值: {thread_memory / 1024 / 1024:.2f} MB")
    print(f"  📊 每个线程: {thread_memory / n / 1024:.2f} KB")

    print(f"\n创建 {n} 个协程...")
    start = time.time()
    coro_memory = asyncio.run(measure_memory_coroutines(n))
    coro_time = time.time() - start
    print(f"  ⏱️  耗时: {coro_time:.2f} 秒")
    print(f"  💾 内存峰值: {coro_memory / 1024 / 1024:.2f} MB")
    print(f"  📊 每个协程: {coro_memory / n / 1024:.2f} KB")

    print(f"\n🎯 对比结果：")
    print(f"  内存效率: 协程比线程轻量 {thread_memory / coro_memory:.1f} 倍")
    print(f"  创建速度: 协程比线程快 {thread_time / coro_time:.1f} 倍")


# ============ 第二部分：上下文切换成本 ============

def demo_context_switch_overhead():
    """演示：线程 vs 协程的上下文切换成本"""
    print("\n" + "="*60)
    print("⚡ 第二部分：上下文切换成本")
    print("="*60)

    iterations = 100000

    # 线程切换
    print(f"\n🔴 线程切换 ({iterations} 次)")
    start = time.time()

    def thread_worker():
        for _ in range(100):
            pass

    threads = []
    for _ in range(100):
        t = threading.Thread(target=thread_worker)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    thread_time = time.time() - start
    print(f"  ⏱️  总耗时: {thread_time:.4f} 秒")
    print(f"  ⚡ 平均每次切换: {thread_time / iterations * 1e6:.2f} 微秒")

    # 协程切换
    print(f"\n🟢 协程切换 ({iterations} 次)")

    async def coro_worker():
        for _ in range(100):
            await asyncio.sleep(0)

    async def run_coros():
        start = time.time()
        coros = [coro_worker() for _ in range(100)]
        await asyncio.gather(*coros)
        return time.time() - start

    coro_time = asyncio.run(run_coros())
    print(f"  ⏱️  总耗时: {coro_time:.4f} 秒")
    print(f"  ⚡ 平均每次切换: {coro_time / iterations * 1e6:.2f} 微秒")

    print(f"\n🎯 对比结果：")
    print(f"  协程切换比线程切换快 {thread_time / coro_time:.1f} 倍")


# ============ 第三部分：事件循环工作流程 ============

async def demo_event_loop_workflow():
    """演示：事件循环如何调度任务"""
    print("\n" + "="*60)
    print("🔄 第三部分：事件循环工作流程")
    print("="*60)

    print("\n📋 任务队列可视化：\n")

    task_names = ["A", "B", "C", "D", "E"]

    async def named_task(name: str, duration: float):
        print(f"  [{name}] 开始执行")
        await asyncio.sleep(duration)
        print(f"  [{name}] await 完成，重新获得控制")
        return f"{name}的结果"

    # 创建任务
    tasks = [named_task(name, 0.1) for name in task_names]

    print("  事件循环开始调度：")
    print("  " + "─" * 50)

    start = time.time()
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start

    print("  " + "─" * 50)
    print(f"  📊 所有任务完成，总耗时: {elapsed:.2f} 秒")
    print(f"  📦 结果: {results}")

    print("\n💡 观察：")
    print("  - 所有任务几乎同时开始（并发）")
    print("  - await 时任务暂停，其他任务继续执行")
    print("  - 总时间约等于最慢任务的时间")


# ============ 第四部分：协程状态机 ============

async def demo_coroutine_state_machine():
    """演示：协程的状态转换"""
    print("\n" + "="*60)
    print("🔧 第四部分：协程状态机")
    print("="*60)

    async def stateful_task():
        """展示协程的状态变化"""
        print("  状态: CREATED → RUNNING")

        await asyncio.sleep(0.1)
        print("  状态: SUSPENDED → RUNNING")

        await asyncio.sleep(0.1)
        print("  状态: SUSPENDED → RUNNING")

        return "状态: FINISHED"

    print("\n🔄 协程状态转换过程：\n")
    result = await stateful_task()
    print(f"  {result}")

    print("\n💡 状态说明：")
    print("  - CREATED: 协程已创建，但尚未开始")
    print("  - RUNNING: 协程正在执行")
    print("  - SUSPENDED: 协程在 await 处暂停")
    print("  - FINISHED: 协程执行完成")


# ============ 第五部分：实际应用场景对比 ============

def blocking_io_simulation():
    """模拟阻塞 IO"""
    time.sleep(0.1)  # 阻塞 100ms


async def non_blocking_io_simulation():
    """模拟非阻塞 IO"""
    await asyncio.sleep(0.1)  # 非阻塞 100ms


def demo_real_world_scenario():
    """演示：实际应用场景的性能差异"""
    print("\n" + "="*60)
    print("🌐 第五部分：实际应用场景")
    print("="*60)

    n = 10

    # 模拟同步版本（阻塞）
    print(f"\n🔴 同步版本：处理 {n} 个请求")
    start = time.time()
    for i in range(n):
        blocking_io_simulation()
    sync_time = time.time() - start
    print(f"  ⏱️  总耗时: {sync_time:.2f} 秒")
    print(f"  📊 每个请求: {sync_time / n:.2f} 秒")

    # 模拟异步版本（非阻塞）
    print(f"\n🟢 异步版本：处理 {n} 个请求")
    start = time.time()
    asyncio.run(asyncio.gather(
        *[non_blocking_io_simulation() for _ in range(n)]
    ))
    async_time = time.time() - start
    print(f"  ⏱️  总耗时: {async_time:.2f} 秒")
    print(f"  📊 每个请求: {async_time / n:.2f} 秒")

    print(f"\n🎯 性能提升：")
    print(f"  异步比同步快 {sync_time / async_time:.1f} 倍")
    print(f"  在处理大量 IO 操作时，差异会更加明显")


# ============ 第六部分：系统信息 ============

def demo_system_info():
    """显示系统相关信息"""
    print("\n" + "="*60)
    print("💻 系统信息")
    print("="*60)

    print(f"\nPython 版本: {sys.version}")
    print(f"平台: {sys.platform}")
    print(f"CPU 核心数: {threading.cpu_count()}")

    if sys.platform.startswith('linux'):
        print("IO 多路复用: epoll")
    elif sys.platform.startswith('darwin'):
        print("IO 多路复用: kqueue")
    elif sys.platform.startswith('win'):
        print("IO 多路复用: IOCP")

    print(f"\n默认递归深度: {sys.getrecursionlimit()}")
    print(f"估算线程栈大小: {sys.getrecursionlimit() * 8 / 1024:.2f} MB")


# ============ 主函数 ============

def main():
    """运行所有演示"""
    print("\n" + "="*60)
    print("🎓 架构师深度讲解：事件循环底层机制")
    print("="*60)

    print("\n本演示将通过可视化方式展示：")
    print("1. 线程 vs 协程的内存消耗")
    print("2. 上下文切换的成本")
    print("3. 事件循环的工作流程")
    print("4. 协程的状态转换")
    print("5. 实际应用场景对比")
    print("6. 系统信息")

    input("\n按回车开始演示...")

    # 1. 系统信息
    demo_system_info()

    # 2. 内存对比
    input("\n按回车继续到内存对比演示...")
    demo_memory_comparison()

    # 3. 上下文切换
    input("\n按回车继续到上下文切换演示...")
    demo_context_switch_overhead()

    # 4. 事件循环
    input("\n按回车继续到事件循环演示...")
    asyncio.run(demo_event_loop_workflow())

    # 5. 状态机
    input("\n按回车继续到协程状态机演示...")
    asyncio.run(demo_coroutine_state_machine())

    # 6. 实际场景
    input("\n按回车继续到实际场景演示...")
    demo_real_world_scenario()

    # 总结
    print("\n" + "="*60)
    print("📝 总结")
    print("="*60)
    print("\n核心要点：")
    print("1. 协程比线程轻量 100-1000 倍（内存）")
    print("2. 协程切换比线程快 10-100 倍（时间）")
    print("3. 事件循环通过 IO 多路复用实现高并发")
    print("4. 异步 IO 在处理大量并发时优势明显")
    print("\n记住：")
    print("- 异步不是万能的，CPU 密集型任务用多进程")
    print("- 避免在异步代码中使用阻塞操作")
    print("- 协程是协作式的，主动让出控制权很重要")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
