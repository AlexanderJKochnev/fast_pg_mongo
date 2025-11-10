# tests/conftest.py

import asyncio
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os
import sys
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.databases.postgres import Base, get_db
from app.databases.mongo import mongodb, get_database, MongoDB, get_mongodb

# Тестовые настройки
TEST_DATABASE_URL = "postgresql+psycopg_async://test_user:test@localhost:2345/test_db"
# TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test@localhost:2345/test_db"
TEST_MONGO_URL = "mongodb://admin:admin@localhost:27027"
TEST_MONGO_DB = "test_db"

# Глобальные переменные для тестовых ресурсов
test_engine = None
TestingSessionLocal = None


@pytest.fixture(scope="session")
def test_database_url():
    return TEST_DATABASE_URL


@pytest.fixture(scope="session")
def test_mongo_url():
    return TEST_MONGO_URL


@pytest.fixture(scope="session")
def test_mongo_db():
    return TEST_MONGO_DB


@pytest.fixture(scope="session")
def event_loop():
    """Создаем event loop для тестов - ОДИН на всю сессию"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_databases():
    """Настройка тестовых баз данных ПЕРЕД запуском тестов"""
    global test_engine, TestingSessionLocal

    print("🔄 Setting up test databases...")

    # Создаем движок
    test_engine = create_async_engine(
        TEST_DATABASE_URL, echo=True, pool_pre_ping=True
    )
    TestingSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    # ПОЛНАЯ ОЧИСТКА И СОЗДАНИЕ - как в рабочем примере
    async with test_engine.begin() as conn:
        from sqlalchemy import text
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        await conn.run_sync(Base.metadata.create_all)

    print("✅ PostgreSQL tables created and cleaned")

    # Очистка MongoDB
    test_mongo = MongoDB()
    await test_mongo.connect(TEST_MONGO_URL, TEST_MONGO_DB)
    collections = await test_mongo.database.list_collection_names()
    for collection_name in collections:
        await test_mongo.database[collection_name].delete_many({})
    await test_mongo.disconnect()

    print("✅ MongoDB cleaned")

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


@pytest.fixture(scope="session")
async def test_mongodb(clean_database, test_mongo_url, test_mongo_db):
    """ Создает тестовый экземпляр MongoDB
    """
    test_mongo = MongoDB()
    await test_mongo.connect(test_mongo_url, test_mongo_db)
    yield test_mongo
    await test_mongo.disconnect()


@pytest.fixture(scope="session")  # , autouse=True)
async def clean_database(test_mongo_url, test_mongo_db):
    """Очищает базу данных перед каждой сессией"""
    test_mongo = MongoDB()
    await test_mongo.connect(test_mongo_url, test_mongo_db)
    if hasattr(test_mongo, test_mongo_db):
        await test_mongo.client.drop_database(test_mongo_db)
        test_mongo.database = test_mongo.client[test_mongo_db]
    await test_mongo.disconnect()


async def override_get_database():
    """Переопределенная зависимость MongoDB для тестов"""
    if not mongodb.client:
        await mongodb.connect(TEST_MONGO_URL, TEST_MONGO_DB)
    return mongodb.database


@pytest.fixture(scope="session")
async def async_client(test_mongodb):
    """Асинхронный тестовый клиент"""
    # Переопределяем зависимости

    async def override_get_mongodb():
        return test_mongodb

    async def override_get_database():
        return test_mongodb.database

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_database] = override_get_database

    async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
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


@pytest.fixture
def test_images_dir():
    """Возвращает путь к директории с тестовыми изображениями"""
    return Path(__file__).parent / "test_images"


@pytest.fixture
def sample_image_paths(test_images_dir):
    """Возвращает пути ко всем тестовым изображениям"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.pdf'}
    image_paths = []

    for file_path in test_images_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            image_paths.append(file_path)

    return image_paths
