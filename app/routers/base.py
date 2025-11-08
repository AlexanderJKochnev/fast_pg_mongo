# app/routers/base.py
# app/routers/base.py
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
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
        
        self.router = APIRouter(prefix = prefix, tags = self.tags)
        self.setup_routes()
    
    def setup_routes(self):
        """Настраивает маршруты"""
        # Create
        self.router.add_api_route(
            "", self.create, methods = ["POST"], response_model = self.read_schema
            )
        
        # Get all с пагинацией
        self.router.add_api_route(
            "", self.get_all, methods = ["GET"], response_model = self.pagination_schema
            )
        
        # Get by ID
        self.router.add_api_route(
            "/{id}", self.get_by_id, methods = ["GET"], response_model = self.read_schema
            )
        
        # Patch
        self.router.add_api_route("/{id}", self.patch, methods = ["PATCH"])
        
        # Delete
        self.router.add_api_route("/{id}", self.delete, methods = ["DELETE"])
        
        # Search с пагинацией
        self.router.add_api_route(
            "/search", self.search, methods = ["GET"], response_model = self.pagination_schema
            )
        
        # Search без пагинации
        self.router.add_api_route(
            "/search_all", self.search_all, methods = ["GET"], response_model = List[self.read_schema]
            )
    
    async def create(self, data, db: AsyncSession = Depends(get_db)):
        """Создание записи"""
        return await self.service.get_or_create(data, db, self.model)
    
    async def get_all(
            self, page: int = Query(1, ge = 1), page_size: int = Query(10, ge = 1, le = 100),
            after_date: Optional[datetime] = None, db: AsyncSession = Depends(get_db)
            ):
        """Получение всех записей с пагинацией"""
        return await self.service.get_all(after_date, page, page_size, db, self.model)
    
    async def get_by_id(self, id: int, db: AsyncSession = Depends(get_db)):
        """Получение записи по ID"""
        return await self.service.get_by_id(id, db, self.model)
    
    async def patch(self, id: int, data, db: AsyncSession = Depends(get_db)):
        """Обновление записи"""
        return await self.service.patch(id, data, db, self.model)
    
    async def delete(self, id: int, db: AsyncSession = Depends(get_db)):
        """Удаление записи"""
        return await self.service.delete(id, self.model, db)
    
    async def search(
            self, query: str = Query(...), page: int = Query(1, ge = 1), page_size: int = Query(10, ge = 1, le = 100),
            db: AsyncSession = Depends(get_db)
            ):
        """Поиск с пагинацией"""
        # Базовая реализация - можно переопределить в дочерних классах
        return await self.service.get_all(None, page, page_size, db, self.model)

    async def search_all(
            self, query: str = Query(...), db: AsyncSession = Depends(get_db)
            ):
        """Поиск без пагинации"""
        # Базовая реализация - можно переопределить в дочерних классах
        return await self.service.get(None, db, self.model)
