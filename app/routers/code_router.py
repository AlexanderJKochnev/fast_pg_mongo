# app/routers/code_router.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.databases.postgres import get_db
from app.models.postgres import Code
from app.routers.base import BaseRouter
from app.schemas.postgres import (CodeCreate, CodeDelete, CodePaginationRead, CodePatch, CodeRead)
from app.services.postgres import CodeService


class CodeRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            prefix="/codes",
            tags=["codes"],
            service=CodeService,
            model=Code,
            create_schema=CodeCreate,
            read_schema=CodeRead,
            patch_schema=CodePatch,
            delete_schema=CodeDelete,
            pagination_schema=CodePaginationRead
        )

    async def create(self, data: CodeCreate, db: AsyncSession = Depends(get_db)):
        """Создание записи"""
        # return await self.service.get_or_create(data, db, self.model)
        return await super().create(data, db)

    async def patch(self, id: int, data: CodePatch, db: AsyncSession = Depends(get_db)):
        """Обновление записи"""
        return await super().patch(id, data, db)
