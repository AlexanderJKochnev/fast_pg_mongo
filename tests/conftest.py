# tests/conftest.py
# flake8:  NOQA: F401
import asyncio
from pathlib import Path
import pytest
import logging
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os
import sys
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.databases.postgres import get_db
from app.models.base import Base
from app.databases.mongo import mongodb, get_database, MongoDB, get_mongodb


scope = "session"
# Тестовые настройки
TEST_DATABASE_URL = "postgresql+psycopg_async://test_user:test@localhost:2345/test_db"
# TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test@localhost:2345/test_db"
TEST_MONGO_URL = "mongodb://admin:admin@localhost:27027"
TEST_MONGO_DB = "test_db"

# Глобальные переменные для тестовых ресурсов
test_engine = None
TestingSessionLocal = None

# --------фикстуры констант-----------

@pytest.fixture(scope=scope)
def base_url():
    return "http://test"

@pytest.fixture(scope=scope)
def test_database_url():
    return TEST_DATABASE_URL


@pytest.fixture(scope="session")
def test_mongo_url():
    return TEST_MONGO_URL


@pytest.fixture(scope="session")
def test_mongo_db():
    return TEST_MONGO_DB


# -----------EVENT_LOOP----------

"""
@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()
"""


@pytest.fixture(scope=scope)
def event_loop(request):
    """
    Создаём отдельный event loop для всей сессии тестов.
    Это предотвращает ошибку "Event loop is closed".
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# ------AUTOUSE FIXTURES-------


@pytest.fixture(autouse=True)
def disable_httpx_logging():
    """Подавляет INFO-логи от httpx и httpcore"""
    loggers_to_silence = ["httpx", "httpx._client", "httpcore"]
    for name in loggers_to_silence:
        logging.getLogger(name).setLevel(logging.WARNING)

# ---- POSTGRESQL ----


@pytest.fixture(scope=scope)
async def mock_engine(test_database_url):
    """
        1. Создает асинхронный движок для тестовой базы данных
        2. Сбрасывает все таблицы в базе данных
        3. Создает таблицы в базе данных на основании мета данных
    """
    engine = create_async_engine(
        test_database_url,
        echo=False,
        # pool_pre_ping=True
        pool_pre_ping=False,  # ❗️ Отключите для async
        pool_recycle=3600,    # Вместо этого используйте pool_recycle
        pool_size=20, max_overflow=0  # !
    )

    # Создает все таблицы в базе данных
    async with engine.begin() as conn:
        # сбрасывает базу данных перед тестированием
        # await conn.run_sync(Base.metadata.drop_all, checkfirst=False, cascade=True)
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope=scope)
async def test_db_session(mock_engine):
    """Создает сессию для тестовой базы данных"""
    AsyncSessionLocal = sessionmaker(
        bind=mock_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    # async with mock_engine.connect() as session:
    async with AsyncSessionLocal() as session:
        try:  # !
            yield session
            await session.commit()  # !  # await session.close()
        except Exception:
            await session.rollback()  # Откат при ошибках
            raise


@pytest.fixture(scope=scope)
async def override_app_dependencies():
    """ Фикстура для переопределения зависимостей приложения
        сохраняет оригинальные зависимости, переписывает их и передает управление,
        затем возвращает назад
    """
    original_overrides = app.dependency_overrides.copy()
    yield app.dependency_overrides
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)


@pytest.fixture(scope=scope)
async def client(test_db_session, override_app_dependencies, base_url):
    """Базовый клиент без авторизации"""
    # Переопределяем зависимость get_db
    async def get_test_db():
        yield test_db_session
    app.dependency_overrides[get_db] = get_test_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=base_url
    ) as ac:
        yield ac
# --------------не классифициорованные


@pytest.fixture(scope="session")  # , autouse=True)
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
        # from sqlalchemy import text
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
async def test_db_session2():
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
