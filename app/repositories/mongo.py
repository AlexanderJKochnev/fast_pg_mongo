# app/repositories/mongo.py
from bson import ObjectId, Binary
from datetime import datetime, timezone
from fastapi import Depends
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.databases.mongo import get_database
from app.config import settings
# from app.models.mongo import FileMetadata  # , ImageResponse

import io
from PIL import Image


class DocumentsRepository:
    def __init__(self, database: AsyncIOMotorDatabase = Depends(get_database)):
        self.db = database
        self.collection = self.db[settings.MONGO_DOCUMENTS]
        self._indexes_created = False
        # self.fields = list(FileMetadata.model_fields.keys())

    async def ensure_indexes(self):
        """Создает индексы только если они не существуют"""
        if self._indexes_created:
            return

        try:
            # Получаем информацию о существующих индексах
            existing_indexes = await self.collection.index_information()
            indexes_to_create = []
            """
            original_url: str
            product_name: str
            filename: Optional[str] = None
            content_type: Optional[str] = None
            size: Optional[int] = None
            """
            # Проверяем какие индексы нужны
            required_indexes = [{"key": [("filename", 1)], "name": "filename_1", "unique": True},
                                {"key": [("original_url", -1), ("_id", 1)], "name": "original_url_1", "unique": True},
                                {"key": [("product_name", -1), ("_id", 1)], "name": "product_name_1", "unique": True}]

            for required_index in required_indexes:
                index_name = required_index["name"]
                if index_name not in existing_indexes:
                    indexes_to_create.append(required_index)
                    print(f"Index {index_name} will be created")
                else:
                    print(f"Index {index_name} already exists")
            # Создаем только недостающие индексы
            if indexes_to_create:
                for index_spec in indexes_to_create:
                    # Создаем индекс с указанием фона, чтобы не блокировать коллекцию
                    await self.collection.create_index(
                        index_spec["key"], name=index_spec["name"], unique=index_spec.get("unique", False),
                        background=True  # Важно: создаем в фоне
                    )
                    print(f"✓ Index {index_spec['name']} created successfully")

            self._indexes_created = True
            print("All indexes are ready")

        except Exception as e:
            print(f"Error ensuring indexes: {e}")

    async def check_indexes_status(self) -> Dict:
        """Проверяет статус всех индексов (для диагностики)"""
        try:
            existing_indexes = await self.collection.index_information()
            return {"total_indexes": len(existing_indexes), "indexes": list(existing_indexes.keys()),
                    "status": "healthy"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _create_thumbnail_png(self, image_content: bytes) -> bytes:
        """Создает thumbnail в формате PNG с сохранением прозрачности"""
        try:
            # Открываем изображение
            image = Image.open(io.BytesIO(image_content))
            original_size = image.size
            print(f"Original image size: {original_size}")

            # Вычисляем новые размеры сохраняя пропорции
            max_size = 300
            if image.width > image.height:
                new_width = max_size
                new_height = int((max_size / image.width) * image.height)
            else:
                new_height = max_size
                new_width = int((max_size / image.height) * image.width)

            print(f"Thumbnail target size: ({new_width}, {new_height})")

            # Ресайзим изображение
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Сохраняем в PNG
            output = io.BytesIO()
            resized_image.save(output, format='PNG', optimize=True)
            result = output.getvalue()

            print(f"Thumbnail created: {len(result)} bytes (was {len(image_content)} bytes)")
            return result
        except Exception as e:
            print(f"Thumbnail creation error: {e}")
            return None

    async def create_document(self, filename: str,
                              content: bytes,
                              content_type: str,
                              description: str) -> Dict[str, Any]:
        await self.ensure_indexes()

        # Создаем thumbnail
        # thumbnail_content = self._create_thumbnail_png(content)
        """
        filename: Optional[str] = None
        content_type: Optional[str] = None
        size: Optional[int] = None
        """

        document = {"filename": filename,
                    "content": Binary(content),  # BinData для MongoDB
                    "description": description,
                    "created_at": datetime.now(timezone.utc), "size": len(content),
                    }

        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def get_document(self, doc_id: str, include_content: bool = True) -> Optional[dict]:
        """ Получить документ """
        await self.ensure_indexes()
        try:
            projection = {"filename": 1,
                          "content": 1,
                          "size": 1,
                          "content_type": 1,
                          }
            result = await self.collection.find_one(
                {"_id": ObjectId(doc_id)}, projection
            )
            if result and "content" in result:
                # Конвертируем Binary обратно в bytes
                result["content"] = result["content"]

            return result
        except Exception as e:
            print(f"Error getting image by ID {doc_id}: {e}")
            return None

    async def delete_image(self, image_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(image_id)})
        return result.deleted_count > 0
