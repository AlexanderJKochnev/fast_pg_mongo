# tests/test_mongo_files.py
# flake8: NOQA: E251 E123 W293
import pytest
from httpx import AsyncClient
import io
from motor.motor_asyncio import AsyncIOMotorClient

pytestmark = pytest.mark.asyncio


async def test_mongo_connection_string(test_mongo_url):
    """ проверка подключения к MONGODB"""
    from motor.motor_asyncio import AsyncIOMotorClient
    try:
        client = AsyncIOMotorClient(test_mongo_url, serverSelectionTimeoutMS = 5000)
        await client.admin.command('ping')
        client.close()
        return True
    except Exception as e:
        pytest.fail(f"MongoDB connection failed: {e}")


@pytest.mark.skip
async def test_mongodb_connection_fixture(test_mongodb, test_mongo_db):
    """ проверка подключения к базе данных
        c фикстурой test_mongodb запускать только один тест за раз - ломает event_loop
    """
    try:
        client: AsyncIOMotorClient = test_mongodb.client
        database: test_mongo_db.database
        await client.admin.command('ping')
    except Exception as e:
        pytest.fail(f"MongoDB connection failed: {e}")
    

# @pytest.mark.skip
async def test_mongodb_crud_direct(test_mongodb, test_mongo_db):
    """
        проверяем методы crud напрямую без fastapi
        запускать
     """
    from bson import ObjectId
    client: AsyncIOMotorClient = test_mongodb.client
    db_name = test_mongo_db
    collection_name = 'test'
    database = client[db_name]
    collection = database[collection_name]
    document = {"filename": 'test_file', "size": 10, "content": 'test_content',
                }
    # create
    result = await collection.insert_one(document)
    id = result.inserted_id
    print(f'{id=}')
    assert isinstance(id, ObjectId), 'method create thru insert_one fault'
    # get by id
    print('test 2 get_by_id')
    result = await collection.find_one({"_id": ObjectId(id)})
    print(result)
    if result:
        result_id = result['_id']
        assert result_id == id, f'{result_id}, {id}'
        assert result == document, 'method get_by_id fault, document received is not equal expected one'
    else:
        assert False, 'method get_by_id fault, document is not found by id'
    # get_metadata_by_id


async def test_upload_file(async_client: AsyncClient):
    """Тест загрузки файла в MongoDB"""
    # Создаем тестовый файл в памяти
    file_content = b"test file content for upload"
    files = {"file": ("test.txt", file_content, "text/plain")}
    
    # Используем follow_redirects=True для автоматического следования за редиректами
    response = await async_client.post(
            "/documents", files = files, follow_redirects = True
            )
    
    assert response.status_code == 200, f"Upload failed: {response.text}"
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