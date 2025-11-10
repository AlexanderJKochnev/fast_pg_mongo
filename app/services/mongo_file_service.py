# app/services/mongo_file_service.py
from typing import List, Optional, Dict, Any
from app.repositories.mongo_file_repository import MongoFileRepository
from app.schemas.mongo_file_schema import MongoFileCreate, MongoFileUpdate
from app.services.base import Service


class MongoFileService(Service):
    """Service для работы с файлами в MongoDB"""

    # Переопределяем repository т.к. для MongoDB другой репозиторий
    repository = None

    @classmethod
    async def create_file(cls, file_data: MongoFileCreate, repository: MongoFileRepository) -> str:
        """Создание файла в MongoDB"""
        return await repository.create(file_data)

    @classmethod
    async def get_file(cls, file_id: str, repository: MongoFileRepository, include_content: bool = False) -> Optional[
            Dict[str, Any]]:
        """Получение файла"""
        if include_content:
            return await repository.get_by_id(file_id)
        else:
            return await repository.get_metadata_by_id(file_id)

    @classmethod
    async def get_file_content(cls, file_id: str, repository: MongoFileRepository) -> Optional[bytes]:
        """Получение только содержимого файла"""
        return await repository.get_file_content(file_id)

    @classmethod
    async def update_file(cls, file_id: str, file_data: MongoFileUpdate, repository: MongoFileRepository) -> bool:
        """Обновление файла"""
        return await repository.update(file_id, file_data)

    @classmethod
    async def delete_file(cls, file_id: str, repository: MongoFileRepository) -> bool:
        """Удаление файла"""
        return await repository.delete(file_id)

    @classmethod
    async def get_all_files(cls, page: int, page_size: int, repository: MongoFileRepository) -> Dict[str, Any]:
        """Получение всех файлов с пагинацией"""
        skip = (page - 1) * page_size
        files = await repository.get_all(skip, page_size)
        total = await repository.count()

        return {"items": files, "total": total, "page": page, "size": page_size,
                "pages": (total + page_size - 1) // page_size}

    @classmethod
    async def search_files(cls, filename: str, page: int, page_size: int, repository: MongoFileRepository) -> Dict[
            str, Any]:
        """Поиск файлов по имени"""
        skip = (page - 1) * page_size
        files = await repository.search_by_filename(filename, skip, page_size)
        total = len(files)

        return {"items": files, "total": total, "page": page, "size": page_size,
                "pages": (total + page_size - 1) // page_size}
