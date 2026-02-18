@echo off
REM FastAPI 学习应用启动脚本 (Windows)

echo 🚀 启动 FastAPI 学习应用...

REM 检查虚拟环境
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 🔧 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 📥 安装依赖...
pip install -r requirements.txt
pip install -r requirements-dev.txt

REM 检查环境变量文件
if not exist ".env" (
    echo ⚙️  创建环境变量文件...
    copy .env.example .env
    echo 请编辑 .env 文件配置必要的环境变量
)

REM 启动应用
echo 🎯 启动应用...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000