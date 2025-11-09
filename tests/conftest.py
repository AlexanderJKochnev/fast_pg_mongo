# tests/conftest.py
# flake8:  NOQA: W291 E402 W292 W293

import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.databases.postgres import Base, get_db
from app.databases.mongo import mongodb, get_database, MongoDB

# Тестовые настройки
TEST_DATABASE_URL = "postgresql+psycopg_async://test_user:test@localhost:2345/test_db"
# TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test@localhost:2345/test_db"
TEST_MONGO_URL = "mongodb://admin:admin@localhost:27027"
TEST_MONGO_DB = "test_db"

# Глобальные переменные для тестовых ресурсов
test_engine = None
TestingSessionLocal = None


@pytest.fixture(scope = "session")
def event_loop():
    """Создаем event loop для тестов - ОДИН на всю сессию"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope = "session", autouse = True)
async def setup_databases():
    """Настройка тестовых баз данных ПЕРЕД запуском тестов"""
    global test_engine, TestingSessionLocal
    
    print("🔄 Setting up test databases...")
    
    # Создаем движок и сессию ОДИН раз на сессию
    test_engine = create_async_engine(
            TEST_DATABASE_URL, echo = True, pool_pre_ping = True
            )
    TestingSessionLocal = async_sessionmaker(
            test_engine, class_ = AsyncSession, expire_on_commit = False, autoflush = False
            )
    
    # Очистка и создание таблиц PostgreSQL
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Очистка MongoDB
    test_db = await override_get_database()
    collections = await test_db.list_collection_names()
    if "files" in collections:
        await test_db.drop_collection("files")
    
    print("✅ Test databases setup completed")
    
    yield
    
    # Cleanup - закрываем движок
    if test_engine:
        await test_engine.dispose()
    print("🧹 Test databases cleanup completed")


async def override_get_db():
    """Переопределенная зависимость для тестов"""
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def override_get_database():
    """Переопределенная зависимость MongoDB для тестов"""
    if not mongodb.client:
        await mongodb.connect(TEST_MONGO_URL, TEST_MONGO_DB)
    return mongodb.database


@pytest.fixture
async def async_client():
    """Асинхронный тестовый клиент"""
    # Переопределяем зависимости
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_database] = override_get_database
    
    async with AsyncClient(
            transport = ASGITransport(app = app), base_url = "http://test"
            ) as client:
        yield client
    
    # Очищаем переопределения
    app.dependency_overrides.clear()


@pytest.fixture
async def test_db_session():
    """Фикстура для тестовой сессии БД"""
    async with TestingSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()