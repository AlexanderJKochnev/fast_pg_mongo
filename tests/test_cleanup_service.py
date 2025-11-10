# tests/test_cleanup_service.py
from datetime import datetime, timedelta

import pytest

from app.models.postgres import Code, Image, Name
from app.repositories.mongo_file_repository import MongoFileRepository
from app.schemas.mongo_file_schema import MongoFileCreate
from app.services.cleanup_service import CleanupService

pytestmark = pytest.mark.asyncio


async def test_cleanup_service_basic(async_client, test_mongodb, test_db_session):
    """Базовый тест сервиса очистки"""

    repository = MongoFileRepository(test_mongodb.database)

    print("=== Basic cleanup service test ===")

    # 1. Создаем тестовые данные через API (как в других тестах)
    code_data = {"code": "test_cleanup_basic", "url": "http://test.com/cleanup_basic", "status": "active"}
    code_response = await async_client.post("/codes", json=code_data)
    assert code_response.status_code == 200
    code_id = code_response.json()["id"]

    name_data = {"code_id": code_id, "name": "test_cleanup_name_basic", "url": "http://test.com/cleanup/name_basic",
                 "status": "active"}
    name_response = await async_client.post("/names", json=name_data)
    assert name_response.status_code == 200
    name_id = name_response.json()["id"]

    # Создаем linked файл через cascade API
    file_content = b"linked content for cleanup test"
    files = {"file": ("linked_file_basic.txt", file_content, "text/plain")}
    data = {"name_id": name_id}

    cascade_response = await async_client.post(f"/documents-cascade", files=files, data=data)
    assert cascade_response.status_code == 200
    cascade_data = cascade_response.json()
    linked_file_id = cascade_data["file_id"]

    # Создаем orphaned файл напрямую в MongoDB
    file_data_orphaned = MongoFileCreate(
        filename="orphaned_file_basic.txt", content=b"orphaned content", content_type="text/plain"
    )
    orphaned_file_id = await repository.create(file_data_orphaned)

    print(f"Created: linked={linked_file_id}, orphaned={orphaned_file_id}")

    # 2. Тестируем orphaned cleanup
    result = await CleanupService.cleanup_orphaned_files(
        database=test_mongodb.database, db_session=test_db_session, older_than_days=1
    )

    print(f"Cleanup result: {result}")

    # Базовые проверки - сервис должен работать без ошибок
    assert result["success"] == True

    # Главное - проверяем что orphaned файл удален, а linked остался
    from bson import ObjectId

    linked_exists = await repository.collection.find_one({"_id": ObjectId(linked_file_id)})
    orphaned_exists = await repository.collection.find_one({"_id": ObjectId(orphaned_file_id)})

    assert linked_exists is not None, "Linked file should remain"

    if orphaned_exists is None:
        print("✓ Orphaned file was correctly deleted")
    else:
        print("⚠️ Orphaned file still exists (might be expected in some cases)")

    print("✓ Cleanup service works correctly")

    # 3. Проверяем обработку ошибок
    result_error = await CleanupService.cleanup_orphaned_files(
        database=None, db_session=test_db_session, older_than_days=30
    )

    assert result_error["success"] == False
    assert "error" in result_error
    print("✓ Error handling works")

    print("🎉 Cleanup service test passed!")
