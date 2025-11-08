# app/routers/rawdata_router.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.databases.postgres import get_db
from app.routers.base import BaseRouter
from app.models.postgres import Rawdata
from app.services.postgres import RawService
from app.schemas.postgres import (
    RawdataCreate, RawdataRead, RawdataPatch, RawdataDelete, RawdataPaginationRead
)


class RawdataRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            prefix="/rawdata",
            tags=["rawdata"],
            service=RawService,
            model=Rawdata,
            create_schema=RawdataCreate,
            read_schema=RawdataRead,
            patch_schema=RawdataPatch,
            delete_schema=RawdataDelete,
            pagination_schema=RawdataPaginationRead
        )

    async def create(self, data: RawdataCreate, db: AsyncSession = Depends(get_db)):
        """Создание записи"""
        return await self.service.get_or_create(data, db, self.model)

    async def patch(self, id: int, data: RawdataPatch, db: AsyncSession = Depends(get_db)):
        """Обновление записи"""
        return await self.service.patch(id, data, db, self.model)
