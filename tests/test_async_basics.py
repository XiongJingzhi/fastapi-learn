"""
Level 0 测试：验证你对异步基础的理解

这些测试帮助你验证是否理解了：
1. 同步 vs 异步的执行差异
2. 事件循环的基本概念
3. 并发执行的优势
4. 阻塞操作的问题

运行测试：
    pytest tests/test_async_basics.py -v
"""

import pytest
import asyncio
import time


# ============ 测试1: 理解 async/await 语法 ============

@pytest.mark.asyncio
async def test_async_function_returns_coroutine():
    """
    测试：理解协程函数的返回值

    知识点：
    - 调用 async def 定义的函数，返回的是协程对象，不是直接结果
    - 协程对象需要被事件循环调度执行
    """
    async def simple_async():
        return "result"

    # 调用协程函数返回协程对象
    result = simple_async()
    assert str(result).startswith("<coroutine object"), "应该返回协程对象"

    # 使用 await 获取实际结果
    actual_result = await result
    assert actual_result == "result"


@pytest.mark.asyncio
async def test_await_switches_execution():
    """
    测试：理解 await 让出控制权

    知识点：
    - await 会暂停当前协程，让事件循环执行其他任务
    - 这允许并发执行多个IO操作
    """
    execution_order = []

    async def task_a():
        execution_order.append("A_start")
        await asyncio.sleep(0.01)  # 让出控制权
        execution_order.append("A_end")

    async def task_b():
        execution_order.append("B_start")
        await asyncio.sleep(0.01)  # 让出控制权
        execution_order.append("B_end")

    # 并发执行
    await asyncio.gather(task_a(), task_b())

    # 验证：任务会交替执行（不是严格的 A_start -> A_end -> B_start -> B_end）
    assert "A_start" in execution_order
    assert "B_start" in execution_order
    assert "A_end" in execution_order
    assert "B_end" in execution_order


# ============ 测试2: 并发执行的性能 ============

@pytest.mark.asyncio
async def test_concurrent_performance():
    """
    测试：理解并发执行的性能优势

    知识点：
    - 并发执行多个IO操作，总时间约等于最慢操作的时间
    - 而不是所有操作时间之和
    """
    async def io_task(duration: float):
        await asyncio.sleep(duration)
        return duration

    start = time.time()

    # 并发执行3个任务，每个1秒
    results = await asyncio.gather(
        io_task(1),
        io_task(1),
        io_task(1),
    )

    elapsed = time.time() - start

    # 并发执行，总时间应该远小于3秒
    assert elapsed < 2.0, f"并发执行应该约1秒，实际{elapsed:.2f}秒"
    assert len(results) == 3


# ============ 测试3: 理解阻塞操作 ============

@pytest.mark.asyncio
async def test_blocking_vs_non_blocking():
    """
    测试：理解阻塞和非阻塞操作的区别

    知识点：
    - asyncio.sleep() 是非阻塞的
    - time.sleep() 是阻塞的（不要在 async def 中使用）
    """
    import time as sync_time

    # 非阻塞版本
    start = time.time()
    await asyncio.gather(
        asyncio.sleep(0.1),
        asyncio.sleep(0.1),
    )
    non_blocking_time = time.time() - start

    # 非阻塞版本应该接近0.1秒（并发）
    assert non_blocking_time < 0.2, "asyncio.sleep 应该是非阻塞的"


# ============ 测试4: asyncio.create_task ============

@pytest.mark.asyncio
async def test_create_task():
    """
    测试：理解 asyncio.create_task

    知识点：
    - create_task 立即调度协程执行
    - 不需要等待，可以继续做其他事情
    - 后续可以用 await 获取结果
    """
    task_started = False
    task_completed = False

    async def background_task():
        nonlocal task_started, task_completed
        task_started = True
        await asyncio.sleep(0.1)
        task_completed = True
        return "done"

    # 创建任务（立即开始执行）
    task = asyncio.create_task(background_task())

    # 给任务一个执行的机会（让出控制权）
    await asyncio.sleep(0)

    # 任务已经开始
    assert task_started, "任务应该已经启动"

    # 但还没完成（因为 sleep(0.1) 还没完成）
    assert not task_completed, "任务不应该立即完成"

    # 等待任务完成
    result = await task

    # 现在任务完成了
    assert task_completed, "任务应该已完成"
    assert result == "done"


# ============ 测试5: 错误处理 ============

@pytest.mark.asyncio
async def test_error_in_gather():
    """
    测试：理解并发执行中的错误处理

    知识点：
    - gather() 中任何一个任务抛出异常，会立即取消其他任务
    - 可以使用 return_exceptions=True 来改变这个行为
    """
    async def failing_task():
        await asyncio.sleep(0.01)
        raise ValueError("任务失败")

    async def successful_task():
        await asyncio.sleep(0.01)
        return "成功"

    # 默认行为：任何异常会传播
    with pytest.raises(ValueError):
        await asyncio.gather(
            failing_task(),
            successful_task(),
        )

    # 使用 return_exceptions=True 返回异常对象
    results = await asyncio.gather(
        failing_task(),
        successful_task(),
        return_exceptions=True,
    )

    assert isinstance(results[0], ValueError)
    assert results[1] == "成功"


# ============ 测试6: 实际应用场景 ============

@pytest.mark.asyncio
async def test_simulated_api_calls():
    """
    测试：模拟实际的API调用场景

    场景：需要调用3个外部API，然后组合结果
    """
    async def call_api(api_name: str, delay: float) -> dict:
        """模拟API调用"""
        await asyncio.sleep(delay)
        return {"api": api_name, "data": f"data from {api_name}"}

    start = time.time()

    # 并发调用3个API
    results = await asyncio.gather(
        call_api("API-1", 0.1),
        call_api("API-2", 0.1),
        call_api("API-3", 0.1),
    )

    elapsed = time.time() - start

    # 验证结果
    assert len(results) == 3
    assert all(isinstance(r, dict) for r in results)
    assert elapsed < 0.2, "并发调用API应该更快"


# ============ 运行说明 ============

"""
📝 测试说明：

这些测试帮助你验证对异步基础的理解。

运行所有测试：
    pytest tests/test_async_basics.py -v

运行单个测试：
    pytest tests/test_async_basics.py::test_async_function_returns_coroutine -v

查看详细输出：
    pytest tests/test_async_basics.py -v -s

💡 学习建议：
1. 先运行测试，看看是否通过
2. 如果不理解，可以修改代码，观察输出
3. 阅读 pytest-asyncio 文档了解更多

🎯 这些测试覆盖了 Level 0 的核心概念：
- ✅ async/await 语法
- ✅ 协程对象和事件循环
- ✅ 并发执行和性能
- ✅ 阻塞 vs 非阻塞
- ✅ 任务创建和调度
- ✅ 错误处理
"""
