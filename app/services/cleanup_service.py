# app/services/cleanup_service.py
from datetime import datetime, timedelta
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.mongo_file_repository import MongoFileRepository
from app.models.postgres import Image
from bson import ObjectId


# app/services/cleanup_service.py

class CleanupService:

    @staticmethod
    async def cleanup_orphaned_files(
            database: AsyncIOMotorDatabase, db_session: AsyncSession, older_than_days: int = 60
    ) -> Dict[str, Any]:
        """Удаление ТОЛЬКО orphaned файлов из MongoDB (без учета возраста)"""
        try:
            repository = MongoFileRepository(database)

            # Получаем все file_id из PostgreSQL которые еще существуют
            result = await db_session.execute(select(Image.file_id).where(Image.file_id.isnot(None)))
            existing_file_ids = {row[0] for row in result}

            print(f"Found {len(existing_file_ids)} existing file IDs in PostgreSQL")
            print(f"Existing file IDs: {list(existing_file_ids)}")

            # Находим все файлы в MongoDB которые НЕ имеют ссылок в PostgreSQL
            orphaned_files = []
            async for document in repository.collection.find({}):
                file_id = str(document["_id"])

                # Проверяем есть ли ссылка в PostgreSQL
                is_orphaned = file_id not in existing_file_ids

                print(f"File {file_id}: is_orphaned={is_orphaned}")

                if is_orphaned:
                    orphaned_files.append(
                        {"file_id": file_id, "filename": document.get("filename"),
                         "created_at": document.get("created_at"), "reason": "orphaned"}
                    )

            print(f"Found {len(orphaned_files)} orphaned files for cleanup: {[f['file_id'] for f in orphaned_files]}")

            # Удаляем найденные файлы
            deleted_count = 0
            deletion_errors = []

            for file_info in orphaned_files:
                try:
                    result = await repository.collection.delete_one({"_id": ObjectId(file_info["file_id"])})
                    if result.deleted_count > 0:
                        deleted_count += 1
                        print(f"✅ Deleted orphaned file: {file_info['filename']}")
                    else:
                        deletion_errors.append(f"Failed to delete {file_info['file_id']}")
                except Exception as e:
                    deletion_errors.append(f"Error deleting {file_info['file_id']}: {str(e)}")

            return {"success": True, "deleted_orphaned_files": deleted_count,
                    "total_orphaned_found": len(orphaned_files), "deletion_errors": deletion_errors}

        except Exception as e:
            return {"success": False, "error": str(e), "deleted_orphaned_files": 0, "total_orphaned_found": 0,
                    "deletion_errors": []}

    @staticmethod
    async def cleanup_old_files_only(
            database: AsyncIOMotorDatabase, older_than_days: int = 30
    ) -> Dict[str, Any]:
        """Удаление только старых файлов из MongoDB без проверки ссылок"""
        try:
            repository = MongoFileRepository(database)
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

            old_files = []
            async for document in repository.collection.find({}):
                created_at = document.get("created_at")
                if created_at and created_at < cutoff_date:
                    old_files.append(
                        {"file_id": str(document["_id"]), "filename": document.get("filename"),
                         "created_at": created_at}
                    )

            deleted_count = 0
            for file_info in old_files:
                try:
                    from bson import ObjectId
                    result = await repository.collection.delete_one({"_id": ObjectId(file_info["file_id"])})
                    if result.deleted_count > 0:
                        deleted_count += 1
                        print(f"✅ Deleted old file: {file_info['filename']}")
                except Exception as e:
                    print(f"Error deleting old file {file_info['file_id']}: {e}")

            return {"success": True, "deleted_old_files": deleted_count, "total_old_found": len(old_files),
                    "cutoff_date": cutoff_date.isoformat()}

        except Exception as e:
            return {"success": False, "error": str(e), "deleted_old_files": 0, "total_old_found": 0}
