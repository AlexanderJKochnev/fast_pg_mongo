# app/routers/name_router.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.databases.postgres import get_db
from app.routers.base import BaseRouter
from app.models.postgres import Name
from app.services.postgres import NameService
from app.schemas.postgres import (
    NameCreate, NameRead, NamePatch, NameDelete, NamePaginationRead
)


class NameRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            prefix="/names",
            tags=["names"],
            service=NameService,
            model=Name,
            create_schema=NameCreate,
            read_schema=NameRead,
            patch_schema=NamePatch,
            delete_schema=NameDelete,
            pagination_schema=NamePaginationRead
        )

    async def create(self, data: NameCreate, db: AsyncSession = Depends(get_db)):
        """Создание записи"""
        return await super().create(data, db)

    async def patch(self, id: int, data: NamePatch, db: AsyncSession = Depends(get_db)):
        """Обновление записи"""
        return await super().patch(id, data, db)
