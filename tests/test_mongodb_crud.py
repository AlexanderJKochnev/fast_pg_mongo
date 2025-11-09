# tests/test_mongo_db_crud.py
# flake8: NOQA: E251 E123 W293
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_mongodb_full_workflow(async_client: AsyncClient):
    """Полный тест всех операций с MongoDB в одной сессии"""
    
    # 1. Тест загрузки файла
    print("=== Testing file upload ===")
    file_content = b"test file content for upload"
    files = {"file": ("test.txt", file_content, "text/plain")}
    
    upload_response = await async_client.post("/documents", files = files)
    assert upload_response.status_code == 200, f"Upload failed: {upload_response.text}"
    upload_data = upload_response.json()
    file_id = upload_data["file_id"]
    print(f"✓ File uploaded with ID: {file_id}")
    
    # 2. Тест получения метаданных файла
    print("=== Testing file metadata retrieval ===")
    metadata_response = await async_client.get(f"/documents/{file_id}")
    assert metadata_response.status_code == 200, f"Metadata failed: {metadata_response.text}"
    metadata_data = metadata_response.json()
    assert metadata_data["filename"] == "test.txt"
    assert metadata_data["file_id"] == file_id
    assert "file_url" in metadata_data
    print("✓ File metadata retrieved successfully")
    
    # 3. Тест получения содержимого файла
    print("=== Testing file content retrieval ===")
    content_response = await async_client.get(f"/documents/{file_id}/content")
    assert content_response.status_code == 200, f"Content failed: {content_response.text}"
    assert content_response.content == file_content
    assert content_response.headers["content-type"].startswith("text/plain")
    print("✓ File content retrieved successfully")
    
    # 4. Тест обновления файла
    print("=== Testing file update ===")
    new_content = b"updated file content"
    update_files = {"file": ("updated_test.txt", new_content, "text/plain")}
    
    update_response = await async_client.patch(f"/documents/{file_id}", files = update_files)
    assert update_response.status_code == 200, f"Update failed: {update_response.text}"
    print("✓ File updated successfully")
    
    # Проверяем обновление содержимого
    updated_content_response = await async_client.get(f"/documents/{file_id}/content")
    assert updated_content_response.status_code == 200
    assert updated_content_response.content == new_content
    print("✓ File content updated verified")
    
    # 5. Тест получения всех файлов
    print("=== Testing get all files ===")
    
    # Загружаем второй файл для теста
    second_file_content = b"second test file content"
    second_files = {"file": ("test2.txt", second_file_content, "text/plain")}
    second_upload_response = await async_client.post("/documents", files = second_files)
    assert second_upload_response.status_code == 200
    second_file_id = second_upload_response.json()["file_id"]
    print(f"✓ Second file uploaded with ID: {second_file_id}")
    
    all_files_response = await async_client.get("/documents")
    assert all_files_response.status_code == 200, f"Get all files failed: {all_files_response.text}"
    all_files_data = all_files_response.json()
    assert "items" in all_files_data
    assert isinstance(all_files_data["items"], list)
    assert len(all_files_data["items"]) >= 2
    print("✓ All files retrieved successfully")
    
    # 6. Тест поиска файлов
    print("=== Testing file search ===")
    # Ищем по обновленному имени файла
    search_file = "test2.txt"
    search_response = await async_client.get("/documents/search", params = {"filename": search_file})
    assert search_response.status_code == 200, f"Search failed: {search_response.text}"
    search_data = search_response.json()
    assert "items" in search_data
    assert isinstance(search_data["items"], list)
    assert len(search_data["items"]) >= 1
    assert search_data["items"][0]["filename"] == search_file
    print("✓ File search works correctly")
    
    # 7. Тест удаления файла
    print("=== Testing file deletion ===")
    delete_response = await async_client.delete(f"/documents/{file_id}")
    assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
    print("✓ File deleted successfully")
    
    # Проверяем, что файл удален
    deleted_check_response = await async_client.get(f"/documents/{file_id}")
    assert deleted_check_response.status_code == 404
    print("✓ File deletion verified")
    
    # 8. Удаляем второй файл для чистоты
    await async_client.delete(f"/documents/{second_file_id}")
    print("✓ Second file cleaned up")
    
    print("🎉 All MongoDB tests passed successfully!")