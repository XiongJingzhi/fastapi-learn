"""
阶段 0.3: 并发执行 - 体验异步带来的性能提升

学习目标：
1. 理解什么是并发（Concurrency）
2. 学会使用 asyncio.gather() 并发执行多个任务
3. 学会使用 asyncio.create_task() 手动创建任务
4. 理解任务并发执行的顺序是不确定的

核心概念：
- 并发（Concurrency）：多个任务在同一时间段内交替执行
- asyncio.gather()：并发执行多个协程，等待它们全部完成
- asyncio.create_task()：立即调度一个协程执行，不等待它完成
- 任务执行顺序：并发任务的执行顺序是不确定的，取决于事件循环的调度

运行这个示例，观察并发执行的随机性！
"""

import asyncio
import random


async def io_task(name: str, duration: float):
    """
    模拟IO操作（如网络请求、数据库查询、文件读写）

    注意：我们使用 asyncio.sleep() 而不是 time.sleep()
    因为 asyncio.sleep() 是异步的，不会阻塞事件循环
    """
    # 模拟不确定的IO时间
    actual_duration = duration + random.uniform(-0.1, 0.1)
    print(f"📤 [{name}] 开始IO操作，预计 {duration:.1f}秒")
    await asyncio.sleep(actual_duration)
    print(f"📥 [{name}] IO操作完成，实际耗时 {actual_duration:.2f}秒")
    return f"{name}的结果"


async def example_1_sequential():
    """示例1: 顺序执行（非并发）"""
    print("\n📌 示例1: 顺序执行（使用 await 逐个等待）")
    print("-" * 50)

    start = asyncio.get_event_loop().time()

    # 顺序执行：每个任务完成后才执行下一个
    result1 = await io_task("任务1", 1.0)
    result2 = await io_task("任务2", 1.0)
    result3 = await io_task("任务3", 1.0)

    end = asyncio.get_event_loop().time()
    print(f"\n⏱️  总耗时: {end - start:.2f} 秒")
    print(f"📦 结果: {result1}, {result2}, {result3}")


async def example_2_gather():
    """示例2: 并发执行（使用 asyncio.gather）"""
    print("\n📌 示例2: 并发执行（使用 asyncio.gather）")
    print("-" * 50)

    start = asyncio.get_event_loop().time()

    # 并发执行：三个任务同时开始
    results = await asyncio.gather(
        io_task("任务1", 1.0),
        io_task("任务2", 1.0),
        io_task("任务3", 1.0),
    )

    end = asyncio.get_event_loop().time()
    print(f"\n⏱️  总耗时: {end - start:.2f} 秒")
    print(f"📦 结果: {results}")


async def example_3_create_task():
    """示例3: 手动创建任务（更细粒度的控制）"""
    print("\n📌 示例3: 手动创建任务（使用 asyncio.create_task）")
    print("-" * 50)

    start = asyncio.get_event_loop().time()

    # 立即创建并调度任务（不等待）
    task1 = asyncio.create_task(io_task("任务1", 1.0))
    print("  ✅ 任务1已创建并调度")

    task2 = asyncio.create_task(io_task("任务2", 1.0))
    print("  ✅ 任务2已创建并调度")

    task3 = asyncio.create_task(io_task("任务3", 1.0))
    print("  ✅ 任务3已创建并调度")

    # 现在三个任务都在并发运行，我们可以做其他事情
    print("\n  🎯 三个任务都在运行，我们可以做其他事情...")

    # 等待所有任务完成
    results = await asyncio.gather(task1, task2, task3)

    end = asyncio.get_event_loop().time()
    print(f"\n⏱️  总耗时: {end - start:.2f} 秒")
    print(f"📦 结果: {results}")


async def example_4_task_group():
    """示例4: 使用 Task Group（Python 3.11+ 推荐）"""
    print("\n📌 示例4: 使用 asyncio.TaskGroup（Python 3.11+）")
    print("-" * 50)

    start = asyncio.get_event_loop().time()

    # TaskGroup 会自动管理任务的生命周期
    results = []
    async with asyncio.TaskGroup() as tg:
        # 创建多个任务
        task1 = tg.create_task(io_task("任务1", 1.0))
        task2 = tg.create_task(io_task("任务2", 1.0))
        task3 = tg.create_task(io_task("任务3", 1.0))

        # 收集结果
        results = [task1, task2, task3]

    end = asyncio.get_event_loop().time()
    print(f"\n⏱️  总耗时: {end - start:.2f} 秒")
    print(f"📦 结果数: {len(results)}")


async def example_5_concurrent_with_processing():
    """示例5: 并发IO + 顺序处理"""
    print("\n📌 示例5: 并发执行IO，然后顺序处理结果")
    print("-" * 50)

    start = asyncio.get_event_loop().time()

    # 第一步：并发执行所有IO任务
    raw_results = await asyncio.gather(
        io_task("数据加载A", 1.0),
        io_task("数据加载B", 1.0),
        io_task("数据加载C", 1.0),
    )

    print(f"\n  🔄 所有IO完成，开始处理数据...")

    # 第二步：顺序处理结果（假设处理有依赖关系）
    processed_results = []
    for result in raw_results:
        # 模拟数据处理（这里用同步代码，因为处理很快）
        processed = f"已处理: {result}"
        processed_results.append(processed)
        print(f"  ✅ {processed}")

    end = asyncio.get_event_loop().time()
    print(f"\n⏱️  总耗时: {end - start:.2f} 秒")
    print(f"📦 处理后的结果: {processed_results}")


def main():
    """运行所有示例"""
    print("\n" + "="*50)
    print("🎓 阶段 0.3: 并发执行 - 异步的性能优势")
    print("="*50)

    asyncio.run(example_1_sequential())
    asyncio.run(example_2_gather())
    asyncio.run(example_3_create_task())

    # Python 3.11+ 才支持 TaskGroup
    import sys
    if sys.version_info >= (3, 11):
        asyncio.run(example_4_task_group())
    else:
        print("\n⚠️  跳过示例4（需要 Python 3.11+）")

    asyncio.run(example_5_concurrent_with_processing())

    print("\n" + "="*50)
    print("💡 核心要点：")
    print("1. asyncio.gather() 是并发执行多个任务的最简单方式")
    print("2. asyncio.create_task() 可以更灵活地控制任务调度")
    print("3. 并发执行可以显著减少IO密集型任务的总时间")
    print("4. 任务执行顺序可能不确定，这是并发的一个特点")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
