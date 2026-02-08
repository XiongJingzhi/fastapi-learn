# Level 0: 并发与异步基础 - 学习记录

## 📚 学习目标

掌握 Python 异步编程的基础知识，为学习 FastAPI 打下坚实基础。

## 🎯 核心概念

1. **同步 vs 异步** - 理解执行模式的差异
2. **事件循环** - 异步程序的"引擎"
3. **并发执行** - 体验异步带来的性能提升
4. **阻塞陷阱** - 学会识别和避免阻塞操作
5. **FastAPI 中的异步** - 将基础应用到实际框架

## 📁 本目录内容

```
study/level0/
├── README.md                  # 本文件：学习概览
├── notes/                     # 学习笔记和费曼讲解
│   ├── 01_sync_vs_async.md
│   ├── 02_event_loop.md
│   ├── 03_concurrency.md
│   ├── 04_blocking_operations.md
│   └── 05_async_with_fastapi.md
├── examples/                  # 代码示例（从 app/examples/ 复制）
│   ├── 01_sync_vs_async.py
│   ├── 02_event_loop.py
│   ├── 03_concurrency.py
│   ├── 04_blocking_operations.py
│   └── 05_async_with_fastapi.py
└── exercises/                 # 练习题和实验
    ├── 01_basic_exercises.md
    ├── 02_intermediate_exercises.md
    └── 03_challenge_projects.md
```

## 📖 学习路径

### 阶段 0.1: 同步 vs 异步

**学习时间**: 10-15分钟
**核心概念**: `async`, `await`, 协程

**学习材料**:
- 笔记: `notes/01_sync_vs_async.md`
- 示例: `examples/01_sync_vs_async.py`
- 运行: `python -m app.examples.01_sync_vs_async`

**完成标准**:
- [ ] 理解同步代码的执行顺序
- [ ] 理解异步代码的并发执行
- [ ] 能够解释 `async def` 和 `await` 的作用

---

### 阶段 0.2: 事件循环

**学习时间**: 15-20分钟
**核心概念**: 事件循环, 协程对象, 任务调度

**学习材料**:
- 笔记: `notes/02_event_loop.md`
- 示例: `examples/02_event_loop.py`
- 运行: `python -m app.examples.02_event_loop`

**完成标准**:
- [ ] 理解事件循环的作用
- [ ] 知道协程对象需要被调度才能执行
- [ ] 理解 `await` 如何让出控制权

---

### 阶段 0.3: 并发执行

**学习时间**: 20-25分钟
**核心概念**: `asyncio.gather()`, `asyncio.create_task()`

**学习材料**:
- 笔记: `notes/03_concurrency.md`
- 示例: `examples/03_concurrency.py`
- 运行: `python -m app.examples.03_concurrency`

**完成标准**:
- [ ] 能够使用 `asyncio.gather()` 并发执行多个任务
- [ ] 理解 `create_task()` 的作用
- [ ] 知道什么时候应该并发，什么时候应该顺序执行

---

### 阶段 0.4: 阻塞陷阱

**学习时间**: 20-25分钟
**核心概念**: 阻塞操作, `run_in_executor()`, 异步库

**学习材料**:
- 笔记: `notes/04_blocking_operations.md`
- 示例: `examples/04_blocking_operations.py`
- 运行: `python -m app.examples.04_blocking_operations`

**完成标准**:
- [ ] 能够识别阻塞操作
- [ ] 知道如何使用异步版本的库
- [ ] 理解 `run_in_executor()` 的作用

---

### 阶段 0.5: FastAPI 中的异步

**学习时间**: 25-30分钟
**核心概念**: FastAPI endpoint, 异步依赖, BackgroundTasks

**学习材料**:
- 笔记: `notes/05_async_with_fastapi.md`
- 示例: `examples/05_async_with_fastapi.py`
- 运行: `uvicorn app.examples.05_async_with_fastapi:app --reload`

**完成标准**:
- [ ] 理解何时使用 `async def`，何时使用 `def`
- [ ] 知道 FastAPI 如何并发处理请求
- [ ] 能够使用 BackgroundTasks

---

## 🧪 验证理解

运行测试验证你的理解：

```bash
pytest tests/test_async_basics.py -v
```

**测试覆盖**:
- ✅ async/await 语法
- ✅ 协程对象和事件循环
- ✅ 并发执行和性能
- ✅ 阻塞 vs 非阻塞
- ✅ 任务创建和调度
- ✅ 错误处理
- ✅ 实际应用场景

---

## 💡 学习建议

### 动手实践
1. **运行每个示例** - 看到输出，建立直觉
2. **修改代码** - 改变参数，观察变化
3. **添加打印** - 理解执行流程
4. **写测试** - 验证你的理解

### 思考问题
- 为什么异步版本比同步版本快？
- `await` 到底在等待什么？
- 什么情况下应该使用并发？
- 如何避免阻塞事件循环？

### 常见误区
- ❌ 认为 `async def` 就会自动并发
- ✅ 需要使用 `await` 或 `asyncio.gather()` 才能并发

- ❌ 在异步代码中使用阻塞操作
- ✅ 使用异步版本的库或 `run_in_executor()`

- ❌ 忘记 `await` 异步函数
- ✅ 调用异步函数时必须使用 `await`

---

## 🎓 完成标准

当你完成以下所有项，就说明 Level 0 达标了：

- [ ] 运行并理解所有 5 个示例
- [ ] 通过所有测试（7/7 通过）
- [ ] 阅读所有学习笔记
- [ ] 完成练习题
- [ ] 能够解释 `async`/`await` 的作用
- [ ] 理解事件循环的基本概念
- [ ] 知道什么是阻塞操作，如何避免
- [ ] 能够编写简单的异步代码
- [ ] 启动了 FastAPI 服务器并测试了 endpoint

---

## 🚀 下一步

完成 Level 0 后，你将准备好进入 **Level 1: FastAPI 作为协议适配层**！

Level 1 将学习：
- 请求参数校验（Query / Path / Body / Header / Cookie）
- 响应处理（JSON / 文件 / Streaming / WebSocket）
- 统一响应格式与错误模型
- HTTP 状态码与语义

**约束**: 不在 endpoint 中写业务逻辑

---

## 📝 学习记录

### 我的笔记
- 学习日期: _____________
- 完成阶段: _____________
- 遇到的问题: _____________
- 我的理解: _____________

### 我的实验
- 尝试过的修改: _____________
- 发现的有趣现象: _____________
- 仍然不理解的: _____________

---

**祝你学习愉快！记住：最好的学习方式是实践！** 🚀
