# tests/test_cascade_files.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
import io


class TestCascadeFileRouter:
    """Асинхронные тесты для каскадной обработки файлов"""
    
    @pytest_asyncio.fixture
    async def test_name_id(self, async_client: AsyncClient):
        """Создает тестовые Code и Name, возвращает name_id"""
        # Создаем Code
        code_data = {"code": "test_code_cascade", "url": "http://example.com/cascade", "status": "pending"}
        code_response = await async_client.post("/codes", json = code_data)
        code_id = code_response.json()["id"]
        
        # Создаем Name
        name_data = {"code_id": code_id, "name": "test_name_cascade", "url": "http://example.com/name/cascade",
                "status": "pending"}
        name_response = await async_client.post("/names", json = name_data)
        return name_response.json()["id"]
    
    async def test_create_cascade_file(self, async_client: AsyncClient, test_name_id: int):
        """Тест создания каскадной записи"""
        file_content = b"cascade file content"
        files = {"file": ("cascade.txt", io.BytesIO(file_content), "text/plain")}
        data = {"name_id": test_name_id}
        
        response = await async_client.post("/files-cascade", files = files, data = data)
        assert response.status_code == 200
        result = response.json()
        assert result["name_id"] == test_name_id
        assert "image_id" in result
        assert "file_id" in result
        return result["image_id"], result["file_id"]
    
    async def test_get_files_by_name(self, async_client: AsyncClient, test_name_id: int):
        """Тест получения файлов по name_id"""
        await self.test_create_cascade_file(async_client, test_name_id)
        
        response = await async_client.get(f"/files-cascade/name/{test_name_id}")
        assert response.status_code == 200
        result = response.json()
        assert "items" in result
        assert "total" in result
        assert len(result["items"]) > 0
        assert result["items"][0]["name_id"] == test_name_id
    
    async def test_get_file_by_image(self, async_client: AsyncClient, test_name_id: int):
        """Тест получения файла по image_id"""
        image_id, file_id = await self.test_create_cascade_file(async_client, test_name_id)
        
        response = await async_client.get(f"/files-cascade/image/{image_id}")
        assert response.status_code == 200
        result = response.json()
        assert result["image_id"] == image_id
        assert result["name_id"] == test_name_id
        assert result["file_id"] == file_id
    
    async def test_delete_files_by_name(self, async_client: AsyncClient, test_name_id: int):
        """Тест удаления файлов по name_id"""
        await self.test_create_cascade_file(async_client, test_name_id)
        
        response = await async_client.delete(f"/files-cascade/name/{test_name_id}")
        assert response.status_code == 200
        result = response.json()
        assert result["deleted_files_from_mongodb"] > 0
        assert result["deleted_images_from_postgresql"] > 0
        
        # Проверяем что файлы удалены
        get_response = await async_client.get(f"/files-cascade/name/{test_name_id}")
        assert get_response.json()["total"] == 0