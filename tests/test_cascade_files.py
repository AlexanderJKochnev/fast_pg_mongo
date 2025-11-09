# tests/test_cascade_files.py
# flake8: NOQA: E251 E123 W293
import pytest
from httpx import AsyncClient
import io
from app.config import settings

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def test_name_id(async_client: AsyncClient):
    """Создает тестовые Code и Name, возвращает name_id"""
    # Создаем Code
    code_data = {"code": "test_code_cascade", "url": "http://example.com/cascade", "status": "pending"}
    code_response = await async_client.post("/codes", json = code_data)
    assert code_response.status_code == 200, f"Code creation failed: {code_response.text}"
    code_id = code_response.json()["id"]
    
    # Создаем Name
    name_data = {"code_id": code_id, "name": "test_name_cascade", "url": "http://example.com/name/cascade",
            "status": "pending"}
    name_response = await async_client.post("/names", json = name_data)
    assert name_response.status_code == 200, f"Name creation failed: {name_response.text}"
    return name_response.json()["id"]


async def test_cascade_files_full_workflow(async_client: AsyncClient, test_name_id: int):
    """Полный тест всех операций с каскадными файлами в одной сессии"""
    
    # 1. Тест создания каскадного файла
    print("=== Testing cascade file creation ===")
    file_content = b"cascade file content"
    files = {"file": ("cascade.txt", file_content, "text/plain")}
    data = {"name_id": test_name_id}
    
    create_response = await async_client.post(f"/{settings.MONGO_DOCUMENTS}-cascade", files = files, data = data)
    assert create_response.status_code == 200, f"Create cascade failed: {create_response.text}"
    create_data = create_response.json()
    image_id = create_data["image_id"]
    file_id = create_data["file_id"]
    print(f"✓ Cascade file created. Image ID: {image_id}, File ID: {file_id}")
    
    # 2. Тест получения файлов по name_id
    print("=== Testing get files by name ===")
    get_by_name_response = await async_client.get(f"/{settings.MONGO_DOCUMENTS}-cascade/name/{test_name_id}")
    assert get_by_name_response.status_code == 200, f"Get files by name failed: {get_by_name_response.text}"
    get_by_name_data = get_by_name_response.json()
    assert "items" in get_by_name_data
    assert "total" in get_by_name_data
    assert len(get_by_name_data["items"]) > 0
    assert get_by_name_data["items"][0]["name_id"] == test_name_id
    print("✓ Files retrieved by name successfully")
    
    # 3. Тест получения файла по image_id
    print("=== Testing get file by image ===")
    get_by_image_response = await async_client.get(f"/{settings.MONGO_DOCUMENTS}-cascade/image/{image_id}")
    assert get_by_image_response.status_code == 200, f"Get file by image failed: {get_by_image_response.text}"
    get_by_image_data = get_by_image_response.json()
    assert get_by_image_data["image_id"] == image_id
    assert get_by_image_data["name_id"] == test_name_id
    assert get_by_image_data["file_id"] == file_id
    print("✓ File retrieved by image successfully")
    
    # 4. Тест удаления файлов по name_id
    print("=== Testing delete files by name ===")
    
    # Сначала создаем еще один файл для теста удаления
    second_file_content = b"second cascade file content"
    second_files = {"file": ("cascade2.txt", second_file_content, "text/plain")}
    second_data = {"name_id": test_name_id}
    
    second_create_response = await async_client.post(
        f"/{settings.MONGO_DOCUMENTS}-cascade", files = second_files, data = second_data
        )
    assert second_create_response.status_code == 200
    print("✓ Second cascade file created for deletion test")
    
    # Теперь удаляем все файлы по name_id
    delete_response = await async_client.delete(f"/{settings.MONGO_DOCUMENTS}-cascade/name/{test_name_id}")
    assert delete_response.status_code == 200, f"Delete files failed: {delete_response.text}"
    delete_data = delete_response.json()
    assert delete_data["deleted_files_from_mongodb"] > 0
    assert delete_data["deleted_images_from_postgresql"] > 0
    print("✓ Files deleted successfully")
    
    # Проверяем что файлы действительно удалены
    verify_delete_response = await async_client.get(f"/{settings.MONGO_DOCUMENTS}-cascade/name/{test_name_id}")
    assert verify_delete_response.status_code == 200
    print(f'=============={test_name_id=}===============')
    assert verify_delete_response.json()["total"] == 0
    print("✓ File deletion verified")
    
    print("🎉 All cascade files tests passed successfully!")