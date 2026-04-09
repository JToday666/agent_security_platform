"""数据库引擎与异步会话工厂。"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.shared.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.SQLALCHEMY_ECHO,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
