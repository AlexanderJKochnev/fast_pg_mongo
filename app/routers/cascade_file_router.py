# app/routers/cascade_file_router.py
import urllib.parse
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.databases.mongo import get_database
from app.databases.postgres import get_db
from app.models.postgres import Image, Name
from app.repositories.mongo_file_repository import MongoFileRepository
from app.services.mongo_file_service import MongoFileService
# from app.services.image_service import ImageService
from app.services.postgres import ImageService, NameService


class CascadeFileRouter:
    def __init__(self):
        self.prefix = f"/{settings.MONGO_DOCUMENTS}-cascade"
        self.tags = [f"{settings.MONGO_DOCUMENTS}-cascade"]

        self.router = APIRouter(prefix=self.prefix, tags=self.tags)
        self.setup_routes()

    def setup_routes(self):
        """Настройка маршрутов для каскадной обработки"""
        self.router.add_api_route(
            "", self.create_cascade_file, methods=["POST"], response_model=dict
        )
        self.router.add_api_route(
            "/name/{name_id}", self.get_files_by_name, methods=["GET"], response_model=dict
        )
        self.router.add_api_route(
            "/image/{image_id}", self.get_file_by_image, methods=["GET"], response_model=dict
        )
        self.router.add_api_route(
            "/cascade/name/{name_id}", self.delete_by_name_id, methods=["DELETE"]
        )
        self.router.add_api_route(
            "/cascade/status/{status}", self.delete_by_name_status, methods=["DELETE"]
        )

    def _generate_file_url(self, file_id: str) -> str:
        base_url = settings.API_BASE_URL.rstrip('/')
        prefix = settings.MONGO_DOCUMENTS
        encoded_file_id = urllib.parse.quote(file_id)
        return f"{base_url}/{prefix}/{encoded_file_id}/content"

    async def create_cascade_file(
            self, name_id: int = Form(...), file: UploadFile = File(...), file_url: Optional[str] = Form(None),
            database=Depends(get_database), db: AsyncSession = Depends(get_db)
    ):
        """Создание каскадной записи: Name -> Image -> MongoDB"""
        try:
            # Создаем репозиторий напрямую
            repository = MongoFileRepository(database)

            # Используем ваш существующий сервис
            name_record = await NameService.get_by_id(name_id, Name, db)
            if not name_record:
                raise HTTPException(status_code=404, detail=f"Name with id {name_id} not found")

            content = await file.read()

            # Используем схему MongoFileCreate вместо словаря
            from app.schemas.mongo_file_schema import MongoFileCreate
            file_data = MongoFileCreate(
                filename=file.filename, content=content,
                content_type=file.content_type or "application/octet-stream"
            )

            file_id = await MongoFileService.create_file(file_data, repository)

            if not file_url:
                file_url = self._generate_file_url(file_id)
            image_data = {"name_id": name_id, "file_id": file_id, "file_url": file_url}
            from app.schemas.postgres import ImageCreate
            image = ImageCreate(**image_data)
            image_record = await ImageService.create_image(image, db, Image)
            # raise HTTPException(status_code=403, detail=f'{image_record=}')
            return {"message": "Cascade file creation successful", "name_id": name_id, "image_id": image_record.id,
                    "file_id": file_id, "filename": file.filename, "file_url": file_url}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Cascade creation failed: {str(e)}")

    async def get_files_by_name(
            self, name_id: int, db: AsyncSession = Depends(get_db), database=Depends(get_database)
    ):
        """Получение всех файлов по name_id"""
        try:
            # Используем ваш существующий метод
            images = await ImageService.get_by_field("name_id", name_id, db, Image)
            repository = MongoFileRepository(database)
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
            raise HTTPException(status_code=500, detail=f"Failed to get files: {str(e)}")

    async def get_file_by_image(
            self, image_id: int, db: AsyncSession = Depends(get_db), database=Depends(get_database)
    ):
        """Получение файла по image_id"""
        try:
            # Используем ваш существующий метод
            repository = MongoFileRepository(database)
            image = await ImageService.get_by_id(image_id, Image, db)
            if not image:
                raise HTTPException(status_code=404, detail=f"Image with id {image_id} not found")

            file_data = await MongoFileService.get_file(image.file_id, repository)
            if not file_data:
                raise HTTPException(status_code=404, detail=f"File {image.file_id} not found in MongoDB")

            return {"name_id": image.name_id, "image_id": image.id, "file_id": image.file_id,
                    "filename": file_data["filename"],
                    "file_url": image.file_url or self._generate_file_url(image.file_id), "size": file_data["size"],
                    "content_type": file_data["content_type"], "created_at": file_data["created_at"]}

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get file: {str(e)}")

    async def delete_by_name_id(
            self, name_id: int, database=Depends(get_database), db: AsyncSession = Depends(get_db)
    ):
        """Удаление по name_id: Name -> Rawdata -> Images -> MongoDB files"""
        try:
            # 1. Получаем все file_id из Images для этого name_id
            from app.models.postgres import Image
            images = await ImageService.get_by_field("name_id", name_id, Image, db)
            file_ids = [image.file_id for image in images if image.file_id]

            # 2. Удаляем файлы из MongoDB
            repository = MongoFileRepository(database)
            deleted_files_count = 0
            for file_id in file_ids:
                try:
                    success = await MongoFileService.delete_file(file_id, repository)
                    if success:
                        deleted_files_count += 1
                except Exception as e:
                    print(f"Failed to delete MongoDB file {file_id}: {e}")

            # 3. Удаляем Name (каскадно удалит Rawdata и Images)
            from app.models.postgres import Name
            delete_result = await NameService.delete(name_id, Name, db)

            return {"message": f"Cascade deletion by name_id {name_id} completed",
                    "deleted_name": delete_result.get('success', False),
                    "deleted_files_from_mongodb": deleted_files_count, "file_ids_deleted": file_ids}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Cascade deletion by name_id failed: {str(e)}")

    async def delete_by_name_status(
            self, status: str, database=Depends(get_database), db: AsyncSession = Depends(get_db)
    ):
        """Удаление по status: Names -> Rawdata -> Images -> MongoDB files"""
        try:
            # 1. Получаем все Names с указанным status
            from app.models.postgres import Name
            names = await NameService.get_by_field("status", status, Name, db)

            if not names:
                return {"message": f"No names found with status '{status}'", "deleted_names": 0,
                        "deleted_files_from_mongodb": 0}

            # 2. Собираем все file_id из всех Images всех найденных Names
            from app.models.postgres import Image
            all_file_ids = []
            deleted_names_count = 0

            for name in names:
                images = await ImageService.get_by_field("name_id", name.id, Image, db)
                file_ids = [image.file_id for image in images if image.file_id]
                all_file_ids.extend(file_ids)

                # Удаляем Name (каскадно удалит Rawdata и Images)
                delete_result = await NameService.delete(name.id, Name, db)
                if delete_result.get('success', False):
                    deleted_names_count += 1

            # 3. Удаляем файлы из MongoDB
            repository = MongoFileRepository(database)
            deleted_files_count = 0
            unique_file_ids = list(set(all_file_ids))  # Убираем дубликаты

            for file_id in unique_file_ids:
                try:
                    success = await MongoFileService.delete_file(file_id, repository)
                    if success:
                        deleted_files_count += 1
                except Exception as e:
                    print(f"Failed to delete MongoDB file {file_id}: {e}")

            return {"message": f"Cascade deletion by status '{status}' completed", "deleted_names": deleted_names_count,
                    "deleted_files_from_mongodb": deleted_files_count, "total_file_ids_found": len(unique_file_ids)}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Cascade deletion by status failed: {str(e)}")


cascade_file_router = CascadeFileRouter().router
