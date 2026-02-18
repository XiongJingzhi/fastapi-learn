#!/bin/bash

# FastAPI 学习应用启动脚本

echo "🚀 启动 FastAPI 学习应用..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ 虚拟环境未激活，尝试手动激活..."
    export PATH="$PWD/venv/bin:$PATH"
fi

# 升级 pip
echo "⬆️  升级 pip..."
python -m pip install --upgrade pip

# 安装依赖
echo "📥 安装依赖..."
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "⚙️  创建环境变量文件..."
    cp .env.example .env
    echo "请编辑 .env 文件配置必要的环境变量"
fi

# 启动应用
echo "🎯 启动应用..."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000