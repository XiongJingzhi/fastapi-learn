#!/usr/bin/env python3
"""
FastAPI 学习应用 - 直接运行脚本
"""

import sys
import subprocess
import os

def check_python_version():
    """检查 Python 版本"""
    if sys.version_info < (3, 8):
        print("❌ 需要 Python 3.8 或更高版本")
        sys.exit(1)
    print(f"✅ Python 版本: {sys.version}")

def create_env_file():
    """创建 .env 文件"""
    if not os.path.exists(".env"):
        print("📝 创建 .env 文件...")
        with open(".env", "w") as f:
            f.write("""# Application Settings
APP_NAME="FastAPI Learning App"
DEBUG=True
VERSION="1.0.0"

# Database
DATABASE_URL="sqlite+aiosqlite:///./app.db"

# Security
SECRET_KEY="your-secret-key-here-change-in-production-123456"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:8000", "http://localhost:3000"]
""")
        print("✅ 已创建 .env 文件")
    else:
        print("✅ .env 文件已存在")

def install_dependencies():
    """安装依赖"""
    print("\n📦 安装依赖包...")

    # 先升级 pip
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                   check=True, capture_output=True)

    # 安装 requirements.txt
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                   check=True)

    # 安装 requirements-dev.txt
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"],
                   check=True)

    print("✅ 依赖安装完成")

def main():
    """主函数"""
    print("🚀 FastAPI 学习应用启动器")
    print("=" * 50)

    # 检查 Python 版本
    check_python_version()

    # 创建环境文件
    create_env_file()

    # 安装依赖
    install_dependencies()

    # 运行应用
    print("\n🎯 启动 FastAPI 应用...")
    print("📖 API 文档: http://localhost:8000/api/v1/docs")
    print("📖 ReDoc 文档: http://localhost:8000/api/v1/redoc")
    print("\n按 Ctrl+C 停止应用\n")

    # 使用 uvicorn 运行应用
    try:
        os.system(f"{sys.executable} -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    except KeyboardInterrupt:
        print("\n👋 应用已停止")

if __name__ == "__main__":
    main()