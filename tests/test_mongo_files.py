# tests/test_mongo_files.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
import io


class TestMongoFileRouter:
    """Асинхронные тесты для MongoDB file router"""
    
    async def test_upload_file(self, async_client: AsyncClient):
        """Тест загрузки файла"""
        file_content = b"test file content"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        
        response = await async_client.post("/files", files = files)
        assert response.status_code == 200
        result = response.json()
        assert "file_id" in result
        assert result["filename"] == "test.txt"
        assert "file_url" in result
        return result["file_id"]
    
    async def test_get_file_metadata(self, async_client: AsyncClient):
        """Тест получения метаданных файла"""
        # Сначала загружаем файл
        file_id = await self.test_upload_file(async_client)
        
        # Получаем метаданные
        response = await async_client.get(f"/files/{file_id}")
        assert response.status_code == 200
        result = response.json()
        assert result["file_id"] == file_id
        assert result["filename"] == "test.txt"
        assert "size" in result
    
    async def test_get_file_content(self, async_client: AsyncClient):
        """Тест получения содержимого файла"""
        # Сначала загружаем файл
        file_content = b"test content for download"
        files = {"file": ("download.txt", io.BytesIO(file_content), "text/plain")}
        upload_response = await async_client.post("/files", files = files)
        file_id = upload_response.json()["file_id"]
        
        # Получаем содержимое
        response = await async_client.get(f"/files/{file_id}/content")
        assert response.status_code == 200
        assert response.content == file_content
        assert response.headers["content-type"] == "text/plain"
    
    async def test_update_file(self, async_client: AsyncClient):
        """Тест обновления файла"""
        # Сначала загружаем файл
        file_id = await self.test_upload_file(async_client)
        
        # Обновляем файл
        new_content = b"updated file content"
        files = {"file": ("updated.txt", io.BytesIO(new_content), "text/plain")}
        
        response = await async_client.patch(f"/files/{file_id}", files = files)
        assert response.status_code == 200
        
        # Проверяем обновление
        content_response = await async_client.get(f"/files/{file_id}/content")
        assert content_response.content == new_content
    
    async def test_delete_file(self, async_client: AsyncClient):
        """Тест удаления файла"""
        # Сначала загружаем файл
        file_id = await self.test_upload_file(async_client)
        
        # Удаляем файл
        response = await async_client.delete(f"/files/{file_id}")
        assert response.status_code == 200
        
        # Проверяем что удален
        get_response = await async_client.get(f"/files/{file_id}")
        assert get_response.status_code == 404
    
    async def test_get_all_files(self, async_client: AsyncClient):
        """Тест получения всех файлов"""
        response = await async_client.get("/files?page=1&page_size=10")
        assert response.status_code == 200
        result = response.json()
        assert "items" in result
        assert "total" in result