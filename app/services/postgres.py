# app/services/postgres.py
from app.services.base import Service
from app.models.postgres import Image, Name


class CodeService(Service):
    pass


class NameService(Service):
    pass


class RawService(Service):
    pass


class ImageService(Service):
    
    @classmethod
    async def create_image(cls, image_data: dict, session, model=Image):
        """Создание записи об изображении"""
        return await cls.get_or_create(image_data, session, model)
