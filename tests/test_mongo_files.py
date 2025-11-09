# tests/test_mongo_files.py
# flake8: NOQA: E251 E123 W293
import pytest
from httpx import AsyncClient
import io

pytestmark = pytest.mark.asyncio


async def test_mongo_connection(async_client: AsyncClient):
    """Тест для проверки подключения к MongoDB"""
    response = await async_client.get("/documents/health")
    print(response.text)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "connected"
    assert data["mongo"] == "ok"
    assert "database" in data


async def test_upload_file(async_client: AsyncClient):
    """Тест загрузки файла в MongoDB"""
    # Создаем тестовый файл в памяти
    file_content = b"test file content for upload"
    files = {"file": ("test.txt", file_content, "text/plain")}
    
    response = await async_client.post("/documents/", files = files)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "file_id" in data
    assert data["filename"] == "test.txt"
    assert "file_url" in data
    return data["file_id"]


async def test_get_file_metadata(async_client: AsyncClient):
    """Тест получения метаданных файла"""
    file_id = await test_upload_file(async_client)
    
    response = await async_client.get(f"/documents/{file_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["filename"] == "test.txt"
    assert data["file_id"] == file_id
    assert "file_url" in data


async def test_get_file_content(async_client: AsyncClient):
    """Тест получения содержимого файла"""
    file_id = await test_upload_file(async_client)
    
    response = await async_client.get(f"/documents/{file_id}/content")
    assert response.status_code == 200, response.text
    assert response.content == b"test file content for upload"
    assert response.headers["content-type"] == "text/plain"


async def test_update_file(async_client: AsyncClient):
    """Тест обновления файла"""
    file_id = await test_upload_file(async_client)
    
    # Обновляем файл
    new_content = b"updated file content"
    files = {"file": ("updated_test.txt", new_content, "text/plain")}
    
    response = await async_client.patch(f"/documents/{file_id}", files = files)
    assert response.status_code == 200, response.text
    
    # Проверяем обновление содержимого
    response = await async_client.get(f"/documents/{file_id}/content")
    assert response.status_code == 200, response.text
    assert response.content == new_content


async def test_delete_file(async_client: AsyncClient, db_session):
    """Тест удаления файла"""
    file_id = await test_upload_file(async_client)
    
    response = await async_client.delete(f"/documents/{file_id}")
    assert response.status_code == 200, response.text
    
    # Проверяем, что файл удален
    response = await async_client.get(f"/documents/{file_id}")
    assert response.status_code == 404, response.text


async def test_get_all_files(async_client: AsyncClient):
    """Тест получения всех файлов"""
    # Загружаем несколько файлов
    file_id1 = await test_upload_file(async_client)
    
    # Загружаем второй файл
    file_content2 = b"second test file content"
    files = {"file": ("test2.txt", file_content2, "text/plain")}
    response = await async_client.post("/documents/", files = files)
    assert response.status_code == 200, response.text
    
    response = await async_client.get("/documents/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 2


async def test_search_files(async_client: AsyncClient):
    """Тест поиска файлов по имени"""
    file_id = await test_upload_file(async_client)
    
    response = await async_client.get("/documents/search", params = {"filename": "test.txt"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1
    assert data["items"][0]["filename"] == "test.txt"