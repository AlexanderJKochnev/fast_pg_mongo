# app/routers/image_router.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.databases.postgres import get_db
from app.routers.base import BaseRouter
from app.models.postgres import Image
from app.services.postgres import ImageService
from app.schemas.postgres import (
    ImageCreate, ImageRead, ImagePatch, ImageDelete, ImagePaginationRead
)


class ImageRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            prefix="/images",
            tags=["images"],
            service=ImageService,
            model=Image,
            create_schema=ImageCreate,
            read_schema=ImageRead,
            patch_schema=ImagePatch,
            delete_schema=ImageDelete,
            pagination_schema=ImagePaginationRead
        )

    async def create(self, data: ImageCreate, db: AsyncSession = Depends(get_db)):
        """Создание записи"""
        return await super().create(data, db)

    async def patch(self, id: int, data: ImagePatch, db: AsyncSession = Depends(get_db)):
        """Обновление записи"""
        return await super().patch(id, data, db)
