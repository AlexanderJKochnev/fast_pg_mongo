# app/routers/cascade_file_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.databases.postgres import get_db
from app.databases.mongo import get_database
from app.repositories.mongo_file_repository import MongoFileRepository
from app.services.mongo_file_service import MongoFileService
# from app.services.image_service import ImageService
from app.services.postgres import NameService, ImageService
from app.models.postgres import Image, Name
from app.config import settings
import urllib.parse


class CascadeFileRouter:
    def __init__(self):
        self.prefix = f"/{settings.MONGO_DOCUMENTS}-cascade"
        self.tags = [f"{settings.MONGO_DOCUMENTS}-cascade"]
        
        self.router = APIRouter(prefix = self.prefix, tags = self.tags)
        self.setup_routes()
    
    def setup_routes(self):
        """Настройка маршрутов для каскадной обработки"""
        self.router.add_api_route("", self.create_cascade_file, methods = ["POST"], response_model = dict)
        self.router.add_api_route("/name/{name_id}", self.get_files_by_name, methods = ["GET"], response_model = dict)
        self.router.add_api_route("/name/{name_id}", self.delete_files_by_name, methods = ["DELETE"])
        self.router.add_api_route("/image/{image_id}", self.get_file_by_image, methods = ["GET"], response_model = dict)
    
    def _generate_file_url(self, file_id: str) -> str:
        base_url = settings.API_BASE_URL.rstrip('/')
        prefix = settings.MONGO_DOCUMENTS
        encoded_file_id = urllib.parse.quote(file_id)
        return f"{base_url}/{prefix}/{encoded_file_id}/content"
    
    async def get_repository(self, database=Depends(get_database)):
        return MongoFileRepository(database)
    
    async def create_cascade_file(
            self, name_id: int = Form(...), file: UploadFile = File(...), file_url: Optional[str] = Form(None),
            repository: MongoFileRepository = Depends(get_repository), db: AsyncSession = Depends(get_db)
            ):
        """Создание каскадной записи: Name -> Image -> MongoDB"""
        try:
            # Используем ваш существующий сервис
            name_record = await NameService.get_by_id(name_id, db, Name)
            if not name_record:
                raise HTTPException(status_code = 404, detail = f"Name with id {name_id} not found")
            
            content = await file.read()
            
            file_data = {"filename": file.filename, "content": content,
                    "content_type": file.content_type or "application/octet-stream"}
            
            file_id = await MongoFileService.create_file(file_data, repository)
            
            if not file_url:
                file_url = self._generate_file_url(file_id)
            
            image_data = {"name_id": name_id, "file_id": file_id, "file_url": file_url}
            
            image_record = await ImageService.create_image(image_data, db, Image)
            
            return {"message": "Cascade file creation successful", "name_id": name_id, "image_id": image_record.id,
                    "file_id": file_id, "filename": file.filename, "file_url": file_url}
        
        except Exception as e:
            raise HTTPException(status_code = 500, detail = f"Cascade creation failed: {str(e)}")
    
    async def get_files_by_name(
            self, name_id: int, db: AsyncSession = Depends(get_db),
            repository: MongoFileRepository = Depends(get_repository)
            ):
        """Получение всех файлов по name_id"""
        try:
            # Используем ваш существующий метод
            images = await ImageService.get_by_field("name_id", name_id, db, Image)
            
            if not images:
                return {"items": [], "total": 0}
            
            cascade_files = []
            for image in images:
                file_data = await MongoFileService.get_file(image.file_id, repository)
                if file_data:
                    cascade_files.append(
                            {"name_id": name_id, "image_id": image.id, "file_id": image.file_id,
                                    "filename": file_data["filename"],
                                    "file_url": image.file_url or self._generate_file_url(image.file_id),
                                    "size": file_data["size"], "content_type": file_data["content_type"],
                                    "created_at": file_data["created_at"]}
                            )
            
            return {"items": cascade_files, "total": len(cascade_files)}
        
        except Exception as e:
            raise HTTPException(status_code = 500, detail = f"Failed to get files: {str(e)}")
    
    async def delete_files_by_name(
            self, name_id: int, db: AsyncSession = Depends(get_db),
            repository: MongoFileRepository = Depends(get_repository)
            ):
        """Удаление всех файлов по name_id"""
        try:
            images = await ImageService.get_by_field("name_id", name_id, db, Image)
            
            if not images:
                raise HTTPException(status_code = 404, detail = f"No files found for name_id {name_id}")
            
            deleted_files = 0
            deleted_images = 0
            
            for image in images:
                # Используем ваш существующий метод delete
                mongo_success = await MongoFileService.delete_file(image.file_id, repository)
                if mongo_success:
                    deleted_files += 1
                
                postgres_result = await ImageService.delete(image.id, Image, db)
                if postgres_result.get('success', False):
                    deleted_images += 1
            
            return {"message": f"Cascade deletion completed", "deleted_files_from_mongodb": deleted_files,
                    "deleted_images_from_postgresql": deleted_images, "name_id": name_id}
        
        except Exception as e:
            raise HTTPException(status_code = 500, detail = f"Cascade deletion failed: {str(e)}")
    
    async def get_file_by_image(
            self, image_id: int, db: AsyncSession = Depends(get_db),
            repository: MongoFileRepository = Depends(get_repository)
            ):
        """Получение файла по image_id"""
        try:
            # Используем ваш существующий метод
            image = await ImageService.get_by_id(image_id, db, Image)
            if not image:
                raise HTTPException(status_code = 404, detail = f"Image with id {image_id} not found")
            
            file_data = await MongoFileService.get_file(image.file_id, repository)
            if not file_data:
                raise HTTPException(status_code = 404, detail = f"File {image.file_id} not found in MongoDB")
            
            return {"name_id": image.name_id, "image_id": image.id, "file_id": image.file_id,
                    "filename": file_data["filename"],
                    "file_url": image.file_url or self._generate_file_url(image.file_id), "size": file_data["size"],
                    "content_type": file_data["content_type"], "created_at": file_data["created_at"]}
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code = 500, detail = f"Failed to get file: {str(e)}")


cascade_file_router = CascadeFileRouter().router
