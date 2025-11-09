# app/repositories/mongo_file_repository.py
from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime
from app.databases.mongo import get_database
from app.schemas.mongo_file_schema import MongoFileCreate, MongoFileUpdate


class MongoFileRepository:
    def __init__(self, database):
        self.collection = database["files"]

    async def create(self, file_data: MongoFileCreate) -> str:
        """Создание файла в MongoDB"""
        document = {"filename": file_data.filename, "size": len(file_data.content),
                    "content": file_data.content, "content_type": file_data.content_type,
                    "created_at": datetime.utcnow()}
        
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)
    
    async def get_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Получение файла по ID"""
        try:
            document = await self.collection.find_one({"_id": ObjectId(file_id)})
            if document:
                return {"file_id": str(document["_id"]), "filename": document["filename"], "size": document["size"],
                        "content": document["content"], "content_type": document["content_type"],
                        "created_at": document["created_at"]}
            return None
        except:
            return None
    
    async def get_metadata_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Получение метаданных файла (без содержимого)"""
        try:
            document = await self.collection.find_one(
                    {"_id": ObjectId(file_id)}, {"content": 0}  # Исключаем поле content
                    )
            if document:
                return {"file_id": str(document["_id"]), "filename": document["filename"], "size": document["size"],
                        "content_type": document["content_type"], "created_at": document["created_at"]}
            return None
        except:
            return None
    
    async def update(self, file_id: str, file_data: MongoFileUpdate) -> bool:
        """Обновление файла"""
        try:
            update_data = {}
            if file_data.filename is not None:
                update_data["filename"] = file_data.filename
            if file_data.content is not None:
                update_data["content"] = file_data.content
                update_data["size"] = len(file_data.content)
            if file_data.content_type is not None:
                update_data["content_type"] = file_data.content_type
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                    {"_id": ObjectId(file_id)}, {"$set": update_data}
                    )
            return result.modified_count > 0
        except:
            return False
    
    async def delete(self, file_id: str) -> bool:
        """Удаление файла"""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(file_id)})
            return result.deleted_count > 0
        except:
            return False
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение всех файлов (метаданные)"""
        cursor = self.collection.find({}, {"content": 0}).skip(skip).limit(limit)
        files = []
        async for document in cursor:
            files.append(
                    {"file_id": str(document["_id"]), "filename": document["filename"], "size": document["size"],
                            "content_type": document["content_type"], "created_at": document["created_at"]}
                    )
        return files
    
    async def count(self) -> int:
        """Подсчет общего количества файлов"""
        return await self.collection.count_documents({})

    async def search_by_filename(self, filename: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Поиск файлов по имени"""
        print(f"Searching for filename: {filename}")  # Отладка
        cursor = self.collection.find(
            {"filename": {"$regex": filename, "$options": "i"}}
            # {"filename": filename}
        ).skip(skip).limit(limit)

        files = []
        async for document in cursor:
            print(f"Found document: {document}")  # Отладка
            # Создаем копию документа без _id и content
            file_data = {k: v for k, v in document.items() if k not in ['_id', 'content']}
            file_data["file_id"] = str(document["_id"])
            files.append(file_data)
        print(f"Total files found: {len(files)}")
        return files

    async def get_file_content(self, file_id: str) -> Optional[bytes]:
        """Получение только содержимого файла"""
        try:
            document = await self.collection.find_one(
                    {"_id": ObjectId(file_id)}, {"content": 1}
                    )
            return document.get("content") if document else None
        except:
            return None