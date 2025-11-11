# tests/test_conftest.py
""" тестируем фикстуры """
import pytest
from sqlalchemy import select, text

pytestmark = pytest.mark.asyncio


async def test_postgres_connection(client, test_db_session):
    """Тест проверяет, что соединение с тестовой базой данных установлено"""
    from app.models.base import Base
    client = client
    print(Base.metadata.schema, '=========================')
    assert False
    # assert test_db_session is not None
    # Выполняем простой запрос к базе данных
    # result = await test_db_session.execute(text("SELECT 1"))
    # value = result.scalar()
    # assert value == 1
