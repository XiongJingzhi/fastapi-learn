from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# 创建 SQLAlchemy 基础类
class Base(DeclarativeBase):
    pass

# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # 在调试模式下显示 SQL
)

# 创建异步会话工厂
async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """
    获取数据库会话的依赖函数

    Yields:
        AsyncSession: 数据库会话
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()