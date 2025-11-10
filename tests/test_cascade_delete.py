# tests/test_cascade_delete.py
# flake8: NOQA: E251 E123 W293
import pytest
from httpx import AsyncClient
import io
from app.config import settings

pytestmark = pytest.mark.asyncio

async def test_cascade_deletion_methods(async_client: AsyncClient):
    """Тесты методов каскадного удаления"""
    
    # Создаем тестовые данные
    code_data = {"code": "test_cascade_del", "url": "http://example.com/cascade_del", "status": "pending"}
    code_response = await async_client.post("/codes", json = code_data)
    code_id = code_response.json()["id"]
    
    name_data = {"code_id": code_id, "name": "test_cascade_delete", "url": "http://example.com/cascade_delete",
                 "status": "to_delete"}
    name_response = await async_client.post("/names", json = name_data)
    name_id = name_response.json()["id"]
    
    # Создаем каскадный файл
    file_content = b"cascade deletion test content"
    files = {"file": ("cascade_del.txt", file_content, "text/plain")}
    data = {"name_id": name_id}
    
    create_response = await async_client.post(f"/{settings.MONGO_DOCUMENTS}-cascade", files = files, data = data)
    assert create_response.status_code == 200
    file_data = create_response.json()
    
    # Тест 1: Удаление по name_id
    print("=== Testing cascade deletion by name_id ===")
    delete_by_id_response = await async_client.delete(f"/{settings.MONGO_DOCUMENTS}-cascade/cascade/name/{name_id}")
    assert delete_by_id_response.status_code == 200
    delete_data = delete_by_id_response.json()
    assert delete_data["deleted_name"] == True
    assert delete_data["deleted_files_from_mongodb"] > 0
    print("✓ Cascade deletion by name_id works")
    
    # Тест 2: Удаление по status
    print("=== Testing cascade deletion by status ===")
    
    # Создаем еще один Name с status "to_delete"
    name_data2 = {"code_id": code_id, "name": "test_cascade_delete2", "url": "http://example.com/cascade_delete2",
                  "status": "to_delete"}
    name_response2 = await async_client.post("/names", json = name_data2)
    name_id2 = name_response2.json()["id"]
    
    # Создаем файл для второго name
    create_response2 = await async_client.post(
        f"/{settings.MONGO_DOCUMENTS}-cascade", files = files, data = {"name_id": name_id2}
        )
    assert create_response2.status_code == 200
    
    # Удаляем по status
    delete_by_status_response = await async_client.delete(
        f"/{settings.MONGO_DOCUMENTS}-cascade/cascade/status/to_delete"
        )
    assert delete_by_status_response.status_code == 200
    status_delete_data = delete_by_status_response.json()
    assert status_delete_data["deleted_names"] > 0
    print("✓ Cascade deletion by status works")
    
    print("🎉 All cascade deletion tests passed!")