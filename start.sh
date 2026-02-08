#!/bin/bash
# FastAPI 学习项目快速启动脚本

echo "=================================="
echo "🚀 FastAPI 学习项目"
echo "=================================="
echo ""

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python 版本: $python_version"
echo ""

# 安装依赖
echo "📦 安装依赖..."
pip install -q -r requirements.txt 2>/dev/null
echo "✅ 依赖安装完成"
echo ""

# 菜单
echo "请选择要运行的内容："
echo ""
echo "【学习】"
echo "1. 📚 打开 Level 0 学习指南（推荐从这里开始）"
echo "2. 📖 查看项目概览"
echo ""
echo "【代码示例】"
echo "3. 运行示例 01: 同步 vs 异步"
echo "4. 运行示例 02: 事件循环"
echo "5. 运行示例 03: 并发执行"
echo "6. 运行示例 04: 阻塞陷阱"
echo "7. 运行示例 05: FastAPI 中的异步"
echo ""
echo "【测试】"
echo "8. 运行 Level 0 测试"
echo ""
echo "0. 退出"
echo ""

read -p "请输入选项 (0-8): " choice

case $choice in
    1)
        echo ""
        echo "📚 打开 Level 0 学习指南..."
        echo "=================================="
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open study/level0/START_HERE.md
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            xdg-open study/level0/START_HERE.md 2>/dev/null || cat study/level0/START_HERE.md
        else
            cat study/level0/START_HERE.md
        fi
        ;;
    2)
        echo ""
        echo "📖 项目概览"
        echo "=================================="
        cat README.md
        ;;
    3)
        echo ""
        echo "运行示例 01: 同步 vs 异步"
        echo "=================================="
        python study/level0/examples/01_sync_vs_async.py
        ;;
    4)
        echo ""
        echo "运行示例 02: 事件循环"
        echo "=================================="
        python study/level0/examples/02_event_loop.py
        ;;
    5)
        echo ""
        echo "运行示例 03: 并发执行"
        echo "=================================="
        python study/level0/examples/03_concurrency.py
        ;;
    6)
        echo ""
        echo "运行示例 04: 阻塞陷阱"
        echo "=================================="
        python study/level0/examples/04_blocking_operations.py
        ;;
    7)
        echo ""
        echo "运行示例 05: FastAPI 中的异步"
        echo "=================================="
        echo "注意：这需要安装 FastAPI 和 uvicorn"
        echo "访问 http://localhost:8000/docs 查看 API 文档"
        echo ""
        uvicorn study.level0.examples.05_async_with_fastapi:app --reload
        ;;
    8)
        echo ""
        echo "运行 Level 0 测试"
        echo "=================================="
        pytest tests/test_async_basics.py -v
        ;;
    0)
        echo "再见！"
        exit 0
        ;;
    *)
        echo "无效选项"
        exit 1
        ;;
esac
