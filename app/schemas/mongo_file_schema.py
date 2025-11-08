# app/schemas/mongo_file_schema.py
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional, List

class MongoFileCreate(BaseModel):
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"

class MongoFileRead(BaseModel):
    file_id: str
    filename: str
    size: int
    created_at: datetime
    content_type: str
    file_url: HttpUrl  # Добавляем динамический URL

class MongoFileUpdate(BaseModel):
    filename: Optional[str] = None
    content: Optional[bytes] = None
    content_type: Optional[str] = None

class MongoFileDelete(BaseModel):
    file_id: str

class MongoFilePaginationRead(BaseModel):
    items: list[MongoFileRead]
    total: int
    page: int
    size: int
    pages: int

# Схемы для каскадной обработки
class CascadeFileCreate(BaseModel):
    name_id: int
    file_url: Optional[str] = None  # Будет сгенерирован автоматически

class CascadeFileRead(BaseModel):
    name_id: int
    image_id: int
    file_id: str
    filename: str
    file_url: HttpUrl
    size: int
    content_type: str
    created_at: datetime

class CascadeFilesResponse(BaseModel):
    items: List[CascadeFileRead]
    total: int