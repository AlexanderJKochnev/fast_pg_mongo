# app/routers/base.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.databases.postgres import get_db


class BaseRouter:
    """Базовый класс роутера"""

    def __init__(
        self, prefix: str, tags: List[str], service, model, create_schema, read_schema, patch_schema, delete_schema,
        pagination_schema, read_schema_relation=None
    ):
        self.prefix = prefix
        self.tags = tags
        self.service = service
        self.model = model
        self.create_schema = create_schema
        self.read_schema = read_schema
        self.patch_schema = patch_schema
        self.delete_schema = delete_schema
        self.pagination_schema = pagination_schema
        self.read_schema_relation = read_schema_relation or read_schema

        self.router = APIRouter(prefix=prefix, tags=self.tags)
        self.setup_routes()

    def setup_routes(self):
        """Настраивает маршруты"""
        # Create
        self.router.add_api_route(
            "", self.create, methods=["POST"], response_model=self.read_schema
        )

        # Get all с пагинацией
        self.router.add_api_route(
            "", self.get_all, methods=["GET"], response_model=self.pagination_schema
        )

        # Search с пагинацией
        self.router.add_api_route(
            "/search", self.search, methods=["GET"], response_model=self.pagination_schema
        )

        # Search без пагинации
        self.router.add_api_route(
            "/search_all", self.search_all, methods=["GET"], response_model=List[self.read_schema]
        )

        # Get by ID
        self.router.add_api_route(
            "/{id}", self.get_by_id, methods=["GET"], response_model=self.read_schema
        )

        # Patch
        self.router.add_api_route("/{id}", self.patch, methods=["PATCH"])

        # Delete
        self.router.add_api_route("/{id}", self.delete, methods=["DELETE"])

    async def create(self, data, db: AsyncSession = Depends(get_db)):
        """Создание записи"""
        return await self.service.get_or_create(data, db, self.model)

    async def get_all(
        self, page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
        db: AsyncSession = Depends(get_db)
    ):
        """Получение всех записей с пагинацией"""
        result = await self.service.get_all(page, page_size, self.model, db)
        return self.pagination_schema(
            items=result["items"], total=result["total"], page=result["page"], page_size=result["page_size"],
            pages=(result["total"] + result["page_size"] - 1) // result["page_size"]
        )

    async def get_by_id(self, id: int, db: AsyncSession = Depends(get_db)):
        """Получение записи по ID"""
        result = await self.service.get_by_id(id, self.model, db)
        if not result:
            raise HTTPException(status_code=404, detail="Record not found")
        return result

    async def patch(self, id: int, data, db: AsyncSession = Depends(get_db)):
        """Обновление записи"""
        result = await self.service.patch(id, data, self.model, db)
        if result.get('success'):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get('message', 'Неизвестная ошибка'))
        return result

    async def delete(self, id: int, db: AsyncSession = Depends(get_db)):
        """Удаление записи"""
        result = await self.service.delete(id, self.model, db)
        if not result.get('success', False):
            raise HTTPException(status_code=404, detail=result.get('message', 'Delete failed'))
        return result
    
    async def search(
            self, query: str = Query(..., description="Search query"),
            field: str = Query("code", description="Field to search in"), page: int = Query(1, ge = 1),
            page_size: int = Query(10, ge = 1, le = 100), db: AsyncSession = Depends(get_db)
            ):
        """Поиск с пагинацией"""
        result = await self.service.search(field, query, page, page_size, self.model, db)
        
        return self.pagination_schema(
                items = result["items"], total = result["total"], page = result["page"],
                page_size = result["page_size"],
                pages = (result["total"] + result["page_size"] - 1) // result["page_size"]
                )

    async def search_all(
        self, query: str = Query(...), db: AsyncSession = Depends(get_db)
    ):
        """Поиск без пагинации"""
        # Базовая реализация - возвращаем все записи
        return await self.service.get(self.model, db)
