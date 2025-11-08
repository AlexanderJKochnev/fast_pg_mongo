# app/services/image_service.py
from app.services.base import Service
from app.repositories.postgres import ImageRepository
from app.models.postgres import Image
from typing import Dict, Any, List


class ImageService(Service):
    """Service для работы с изображениями (PostgreSQL)"""
    repository = ImageRepository

    @classmethod
    async def create_image(cls, image_data: Dict[str, Any], db, model=Image):
        """Создание записи об изображении"""
        return await cls.get_or_create(image_data, db, model)
    
    @classmethod
    async def get_by_field(cls, field_name: str, field_value: Any, db, model=Image) -> List:
        """Поиск записей по полю"""
        # Реализация зависит от вашего базового репозитория
        # Примерная реализация:
        from app.repositories.base import Repository
        return await Repository.get_by_field(field_name, field_value, model, db)
    
    @classmethod
    async def delete(cls, id: int, model=Image, db=None) -> bool:
        """Удаление записи"""
        result = await super().delete(id, model, db)
        return result.get('success', False) if isinstance(result, dict) else result