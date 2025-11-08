# tests/test_names.py
import pytest
import pytest_asyncio
from httpx import AsyncClient


class TestNameRouter:
    """Асинхронные тесты для Name router"""
    
    @pytest_asyncio.fixture
    async def test_code_id(self, async_client: AsyncClient):
        """Создает тестовый Code и возвращает его ID"""
        code_data = {"code": "test_code_for_name", "url": "http://example.com/code_for_name", "status": "pending"}
        response = await async_client.post("/codes", json = code_data)
        return response.json()["id"]
    
    @pytest_asyncio.fixture
    async def test_name_data(self, test_code_id: int):
        return {"code_id": test_code_id, "name": "test_name_1", "url": "http://example.com/name/1", "status": "pending"}
    
    async def test_create_name(self, async_client: AsyncClient, test_name_data: dict):
        """Тест создания Name"""
        response = await async_client.post("/names", json = test_name_data)
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == test_name_data["name"]
        assert result["code_id"] == test_name_data["code_id"]
        assert "id" in result
        return result["id"]
    
    async def test_get_name_by_id(self, async_client: AsyncClient, test_name_data: dict):
        """Тест получения Name по ID"""
        # Создаем Name
        create_response = await async_client.post("/names", json = test_name_data)
        name_id = create_response.json()["id"]
        
        # Получаем по ID
        response = await async_client.get(f"/names/{name_id}")
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == name_id
        assert result["name"] == test_name_data["name"]
    
    async def test_get_all_names(self, async_client: AsyncClient):
        """Тест получения всех Names"""
        response = await async_client.get("/names?page=1&page_size=10")
        assert response.status_code == 200
        result = response.json()
        assert "items" in result
        assert "total" in result
    
    async def test_patch_name(self, async_client: AsyncClient, test_name_data: dict):
        """Тест обновления Name"""
        # Сначала создаем запись
        create_response = await async_client.post("/names", json = test_name_data)
        name_id = create_response.json()["id"]
        
        # Обновляем
        update_data = {"status": "done", "name": "updated_name"}
        response = await async_client.patch(f"/names/{name_id}", json = update_data)
        assert response.status_code == 200
        result = response.json()
        assert result["success"] == True
        
        # Проверяем обновление
        get_response = await async_client.get(f"/names/{name_id}")
        updated_name = get_response.json()
        assert updated_name["status"] == "done"
        assert updated_name["name"] == "updated_name"
    
    async def test_delete_name(self, async_client: AsyncClient, test_name_data: dict):
        """Тест удаления Name"""
        # Сначала создаем запись
        create_response = await async_client.post("/names", json = test_name_data)
        name_id = create_response.json()["id"]
        
        # Удаляем
        response = await async_client.delete(f"/names/{name_id}")
        assert response.status_code == 200
        result = response.json()
        assert result["success"] == True
        
        # Проверяем что удален
        get_response = await async_client.get(f"/names/{name_id}")
        assert get_response.status_code == 404