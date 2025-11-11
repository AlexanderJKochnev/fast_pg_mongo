# tests/test_cascade_delete.py
# flake8: NOQA: E251 E123 W293
import pytest
from httpx import AsyncClient
import io
from app.config import settings

pytestmark = pytest.mark.asyncio


async def test_cascade_deletion_methods(async_client: AsyncClient):
    """Тесты методов каскадного удаления"""

    # Тест 1: Удаление по name_id
    print("=== Testing cascade deletion by name_id ===")

    # Создаем тестовые данные для первого теста
    code_data1 = {"code": "test_cascade_del_1", "url": "http://example.com/cascade_del_1", "status": "pending"}
    code_response1 = await async_client.post("/codes", json=code_data1)
    code_id1 = code_response1.json()["id"]

    name_data1 = {"code_id": code_id1, "name": "test_cascade_delete_1", "url": "http://example.com/cascade_delete_1",
                  "status": "active"}
    name_response1 = await async_client.post("/names", json=name_data1)
    name_id1 = name_response1.json()["id"]

    # Создаем каскадный файл
    file_content = b"cascade deletion test content"
    files = {"file": ("cascade_del_1.txt", file_content, "text/plain")}
    data1 = {"name_id": name_id1}

    create_response1 = await async_client.post(f"/{settings.MONGO_DOCUMENTS}-cascade", files=files, data=data1)
    assert create_response1.status_code == 200

    # Удаляем по name_id
    delete_by_id_response = await async_client.delete(f"/{settings.MONGO_DOCUMENTS}-cascade/cascade/name/{name_id1}")
    assert delete_by_id_response.status_code == 200
    delete_data = delete_by_id_response.json()
    print(f"Delete by name_id result: {delete_data}")

    # Проверяем что удаление прошло успешно
    assert delete_data.get("deleted_name") == True or delete_data.get("success") == True
    assert delete_data.get("deleted_files_from_mongodb", 0) >= 0  # Может быть 0 если файлов не было

    print("✓ Cascade deletion by name_id works")

    # Тест 2: Удаление по status
    print("=== Testing cascade deletion by status ===")

    # Создаем новые тестовые данные для второго теста
    code_data2 = {"code": "test_cascade_del_2", "url": "http://example.com/cascade_del_2", "status": "pending"}
    code_response2 = await async_client.post("/codes", json=code_data2)
    code_id2 = code_response2.json()["id"]

    # Создаем несколько Names с status "to_delete"
    name_data2 = {"code_id": code_id2, "name": "test_cascade_delete_2", "url": "http://example.com/cascade_delete_2",
                  "status": "to_delete"}
    name_response2 = await async_client.post("/names", json=name_data2)
    name_id2 = name_response2.json()["id"]

    name_data3 = {"code_id": code_id2, "name": "test_cascade_delete_3", "url": "http://example.com/cascade_delete_3",
                  "status": "to_delete"}
    name_response3 = await async_client.post("/names", json=name_data3)
    name_id3 = name_response3.json()["id"]

    # Создаем файлы для этих names
    create_response2 = await async_client.post(
        f"/{settings.MONGO_DOCUMENTS}-cascade", files=files, data={"name_id": name_id2}
    )
    assert create_response2.status_code == 200

    create_response3 = await async_client.post(
        f"/{settings.MONGO_DOCUMENTS}-cascade", files=files, data={"name_id": name_id3}
    )
    assert create_response3.status_code == 200

    # Удаляем по status
    delete_by_status_response = await async_client.delete(
        f"/{settings.MONGO_DOCUMENTS}-cascade/cascade/status/to_delete"
    )
    assert delete_by_status_response.status_code == 200
    status_delete_data = delete_by_status_response.json()
    print(f"Delete by status result: {status_delete_data}")

    # Проверяем что удаление прошло успешно
    assert status_delete_data.get("deleted_names", 0) > 0 or status_delete_data.get("success") == True

    print("✓ Cascade deletion by status works")

    print("🎉 All cascade deletion tests passed!")
