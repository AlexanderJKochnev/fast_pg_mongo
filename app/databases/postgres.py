# app/databases/postgres.py
from sqlalchemy.ext.asyncio import (create_async_engine,
                                    async_sessionmaker,
                                    AsyncEngine,
                                    AsyncSession)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# from sqlalchemy.orm import declarative_base
from app.config import settings
from contextlib import asynccontextmanager
from app.models.base import Base


# 1.1.    Асинхронный двигатель
engine: AsyncEngine = create_async_engine(settings.database_url,
                                          echo=settings.DB_ECHO_LOG,
                                          pool_pre_ping=True)

# 1.2. Фабрика асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


# 1.3. Зависимость для внедроения в routes
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# 2.1. строка для синхронного подключения postgresql
sync_database_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

# 2.2. Синхронный двигатель
engine_sync = create_engine(
    sync_database_url,
    echo=settings.DB_ECHO_LOG,
    pool_pre_ping=True,
)

# 2.3. Синхронная фабрика сессий
SessionLocalSync = sessionmaker(autocommit=False, autoflush=False, bind=engine_sync)


# 2.4. Зависисмость для внедения в routes
def get_db_sync():
    db = SessionLocalSync()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """Инициализация БД - создание таблиц"""
    # Импортируем все модели
    # from app.models.postgres import Code, Name, Rawdata, Image

    # Создаем таблицы через движок
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ База данных инициализирована")


@asynccontextmanager
async def get_db_for_init():
    """Специальная зависимость для инициализации"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


print(f"Base в databases/postgres.py: {Base}")
