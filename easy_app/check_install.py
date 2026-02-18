#!/usr/bin/env python3
"""
检查安装是否正确
"""

import sys

def check_python_version():
    """检查 Python 版本"""
    print(f"Python 版本: {sys.version}")
    if sys.version_info < (3, 8):
        print("❌ 需要 Python 3.8 或更高版本")
        return False
    print("✅ Python 版本符合要求")
    return True

def check_packages():
    """检查必要的包"""
    package_mapping = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "sqlalchemy": "sqlalchemy",
        "alembic": "alembic",
        "pydantic": "pydantic",
        "pydantic_settings": "pydantic_settings",
        "python_jose": "jose",
        "passlib": "passlib",
        "aiosqlite": "aiosqlite"
    }

    all_installed = True

    for package_name, import_name in package_mapping.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} 未安装")
            all_installed = False

    return all_installed

def main():
    """主函数"""
    print("🔍 检查 FastAPI 学习应用安装\n")

    # 检查 Python 版本
    if not check_python_version():
        sys.exit(1)

    print("\n📦 检查依赖包...")
    if not check_packages():
        print("\n请运行以下命令安装依赖：")
        print("pip install -r requirements.txt")
        sys.exit(1)

    print("\n✅ 所有检查通过！")
    print("\n🚀 运行应用：")
    print("python3 run.py")
    print("\n或：")
    print("python3 -m uvicorn app.main:app --reload")

if __name__ == "__main__":
    main()