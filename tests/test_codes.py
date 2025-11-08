# tests/test_codes.py
import pytest

pytestmark = pytest.mark.asyncio


async def test_create_code(async_client):
    """Тест создания Code"""
    from app.schemas.postgres import CodeCreate
    test_code_data = {"code": "test_code_1", "url": "http://example.com/1", "status": "pending"}
    try:
        _ = CodeCreate(**test_code_data)
    except Exception as e:
        assert False, f'ошибка валидации {e}'
    response = await async_client.post("/codes", json=test_code_data)
    assert response.status_code == 200
    result = response.json()
    assert result["code"] == test_code_data["code"]
    assert result["url"] == test_code_data["url"]
    assert "id" in result


async def test_create_code_duplicate(async_client):
    """Тест создания дубликата Code"""
    test_code_data = {"code": "test_code_duplicate", "url": "http://example.com/duplicate", "status": "pending"}
    
    # Первое создание
    response1 = await async_client.post("/codes", json = test_code_data)
    assert response1.status_code == 200
    
    # Второе создание с теми же данными
    response2 = await async_client.post("/codes", json = test_code_data)
    assert response2.status_code == 200


async def test_get_code_by_id(async_client):
    """Тест получения Code по ID"""
    # Сначала создаем запись
    test_code_data = {"code": "test_code_get", "url": "http://example.com/get", "status": "pending"}
    create_response = await async_client.post("/codes", json = test_code_data)
    code_id = create_response.json()["id"]
    
    # Получаем по ID
    response = await async_client.get(f"/codes/{code_id}")
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == code_id
    assert result["code"] == test_code_data["code"]


async def test_get_code_not_found(async_client):
    """Тест получения несуществующего Code"""
    response = await async_client.get("/codes/99999")
    assert response.status_code == 404


async def test_get_all_codes(async_client):
    """Тест получения всех Codes с пагинацией"""
    # Создаем несколько записей
    for i in range(3):
        data = {"code": f"test_code_all_{i}", "url": f"http://example.com/all_{i}", "status": "pending"}
        await async_client.post("/codes", json = data)
    
    response = await async_client.get("/codes?page=1&page_size=10")
    assert response.status_code == 200
    result = response.json()
    assert "items" in result
    assert "total" in result
    assert "page" in result
    assert "page_size" in result
    assert len(result["items"]) >= 3


async def test_patch_code(async_client):
    """Тест обновления Code"""
    # Сначала создаем запись
    test_code_data = {"code": "test_code_patch", "url": "http://example.com/patch", "status": "pending"}
    create_response = await async_client.post("/codes", json = test_code_data)
    code_id = create_response.json()["id"]
    
    # Обновляем
    update_data = {"status": "done", "url": "http://example.com/updated"}
    response = await async_client.patch(f"/codes/{code_id}", json = update_data)
    assert response.status_code == 200
    result = response.json()
    assert result["success"] == True
    
    # Проверяем обновление
    get_response = await async_client.get(f"/codes/{code_id}")
    updated_code = get_response.json()
    assert updated_code["status"] == "done"
    assert updated_code["url"] == "http://example.com/updated"


async def test_patch_code_not_found(async_client):
    """Тест обновления несуществующего Code"""
    update_data = {"status": "done"}
    response = await async_client.patch("/codes/99999", json = update_data)
    assert response.status_code == 200
    result = response.json()
    assert result["success"] == False


async def test_delete_code(async_client):
    """Тест удаления Code"""
    # Сначала создаем запись
    test_code_data = {"code": "test_code_delete", "url": "http://example.com/delete", "status": "pending"}
    create_response = await async_client.post("/codes", json = test_code_data)
    code_id = create_response.json()["id"]
    
    # Удаляем
    response = await async_client.delete(f"/codes/{code_id}")
    assert response.status_code == 200
    result = response.json()
    assert result["success"] == True
    
    # Проверяем что удален
    get_response = await async_client.get(f"/codes/{code_id}")
    assert get_response.status_code == 404


async def test_delete_code_not_found(async_client):
    """Тест удаления несуществующего Code"""
    response = await async_client.delete("/codes/99999")
    assert response.status_code == 200
    result = response.json()
    assert result["success"] == False


async def test_search_codes(async_client):
    """Тест поиска Codes"""
    response = await async_client.get("/codes/search?query=test&page=1&page_size=10")
    assert response.status_code == 200
    result = response.json()
    assert "items" in result
    assert "total" in result