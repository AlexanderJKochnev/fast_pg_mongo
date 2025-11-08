# app/routers/mongo_file_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import Response
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.databases.postgres import get_db
from app.databases.mongo import get_database
from app.repositories.mongo_file_repository import MongoFileRepository
from app.services.mongo_file_service import MongoFileService
from app.services.image_service import ImageService
from app.schemas.mongo_file_schema import MongoFileCreate, MongoFileUpdate
from app.models.postgres import Image
from app.config import settings
import urllib.parse


class MongoFileRouter:
    def __init__(self):
        self.prefix = f"/{settings.MONGO_DOCUMENTS}"
        self.tags = [settings.MONGO_DOCUMENTS]
        
        self.router = APIRouter(prefix = self.prefix, tags = self.tags)
        self.setup_routes()
    
    def setup_routes(self):
        """Настройка маршрутов"""
        self.router.add_api_route("", self.upload_file, methods = ["POST"], response_model = dict)
        self.router.add_api_route("/{file_id}", self.get_file, methods = ["GET"], response_model = dict)
        self.router.add_api_route("/{file_id}/content", self.get_file_content, methods = ["GET"])
        self.router.add_api_route("/{file_id}", self.update_file_upload, methods = ["PATCH"])
        self.router.add_api_route("/{file_id}", self.delete_file, methods = ["DELETE"])
        self.router.add_api_route("", self.get_all_files, methods = ["GET"], response_model = dict)
        self.router.add_api_route("/search", self.search_files, methods = ["GET"], response_model = dict)
        self.router.add_api_route("/{file_id}/link-to-postgres", self.link_to_postgres, methods = ["POST"])
    
    def _generate_file_url(self, file_id: str) -> str:
        """Генерация динамического URL для файла"""
        base_url = settings.API_BASE_URL.rstrip('/')
        prefix = settings.MONGO_DOCUMENTS
        encoded_file_id = urllib.parse.quote(file_id)
        return f"{base_url}/{prefix}/{encoded_file_id}/content"
    
    async def get_repository(self, database=Depends(get_database)):
        return MongoFileRepository(database)
    
    async def upload_file(
            self, file: UploadFile = File(...), repository: MongoFileRepository = Depends(get_repository)
            ):
        """Загрузка файла через UploadFile"""
        try:
            content = await file.read()
            
            file_data = MongoFileCreate(
                    filename = file.filename, content = content,
                    content_type = file.content_type or "application/octet-stream"
                    )
            
            file_id = await MongoFileService.create_file(file_data, repository)
            file_url = self._generate_file_url(file_id)
            
            return {"file_id": file_id, "filename": file.filename, "file_url": file_url,
                    "message": "File uploaded successfully"}
        except Exception as e:
            raise HTTPException(status_code = 500, detail = f"Upload failed: {str(e)}")
    
    async def get_file(
            self, file_id: str, repository: MongoFileRepository = Depends(get_repository)
            ):
        """Получение файла (без содержимого)"""
        file_data = await MongoFileService.get_file(file_id, repository)
        if not file_data:
            raise HTTPException(status_code = 404, detail = "File not found")
        
        file_data["file_url"] = self._generate_file_url(file_id)
        return file_data
    
    async def get_file_content(
            self, file_id: str, repository: MongoFileRepository = Depends(get_repository)
            ):
        """Получение содержимого файла"""
        content = await MongoFileService.get_file_content(file_id, repository)
        if not content:
            raise HTTPException(status_code = 404, detail = "File not found")
        
        file_meta = await MongoFileService.get_file(file_id, repository)
        media_type = file_meta.get("content_type", "application/octet-stream")
        
        return Response(content = content, media_type = media_type)
    
    async def update_file_upload(
            self, file_id: str, file: UploadFile = File(None), filename: Optional[str] = Form(None),
            repository: MongoFileRepository = Depends(get_repository)
            ):
        """Обновление файла через UploadFile"""
        update_data = {}
        
        if file:
            content = await file.read()
            update_data["content"] = content
            update_data["content_type"] = file.content_type or "application/octet-stream"
            if not filename:
                update_data["filename"] = file.filename
        
        if filename:
            update_data["filename"] = filename
        
        if not update_data:
            raise HTTPException(status_code = 400, detail = "No data provided for update")
        
        file_update = MongoFileUpdate(**update_data)
        success = await MongoFileService.update_file(file_id, file_update, repository)
        
        if not success:
            raise HTTPException(status_code = 404, detail = "File not found or update failed")
        return {"message": "File updated successfully"}
    
    async def delete_file(
            self, file_id: str, repository: MongoFileRepository = Depends(get_repository),
            db: AsyncSession = Depends(get_db)
            ):
        """Удаление файла с проверкой связей в PostgreSQL"""
        # Используем ваш существующий метод
        images_with_file = await ImageService.get_by_field("file_id", file_id, db, Image)
        if images_with_file:
            raise HTTPException(
                    status_code = 400, detail = "Cannot delete file: it is referenced in PostgreSQL"
                    )
        
        success = await MongoFileService.delete_file(file_id, repository)
        if not success:
            raise HTTPException(status_code = 404, detail = "File not found")
        return {"message": "File deleted successfully"}
    
    async def get_all_files(
            self, page: int = Query(1, ge = 1), page_size: int = Query(10, ge = 1, le = 100),
            repository: MongoFileRepository = Depends(get_repository)
            ):
        """Получение всех файлов с пагинацией"""
        result = await MongoFileService.get_all_files(page, page_size, repository)
        
        for item in result["items"]:
            item["file_url"] = self._generate_file_url(item["file_id"])
        
        return result
    
    async def search_files(
            self, filename: str = Query(...), page: int = Query(1, ge = 1),
            page_size: int = Query(10, ge = 1, le = 100), repository: MongoFileRepository = Depends(get_repository)
            ):
        """Поиск файлов по имени с пагинацией"""
        result = await MongoFileService.search_files(filename, page, page_size, repository)
        
        for item in result["items"]:
            item["file_url"] = self._generate_file_url(item["file_id"])
        
        return result
    
    async def link_to_postgres(
            self, file_id: str, name_id: int, file_url: Optional[str] = None,
            repository: MongoFileRepository = Depends(get_repository), db: AsyncSession = Depends(get_db)
            ):
        """Создание связи между MongoDB файлом и PostgreSQL записью"""
        file_data = await MongoFileService.get_file(file_id, repository)
        if not file_data:
            raise HTTPException(status_code = 404, detail = "File not found in MongoDB")
        
        if not file_url:
            file_url = self._generate_file_url(file_id)
        
        # Используем ваш существующий сервис
        image_data = {"name_id": name_id, "file_id": file_id, "file_url": file_url}
        
        result = await ImageService.create_image(image_data, db, Image)
        
        return {"message": "File linked to PostgreSQL successfully", "postgres_id": result.id, "mongo_file_id": file_id,
                "file_url": file_url}


mongo_file_router = MongoFileRouter().router
