# app/models/mongo.py
""" pydantic models for mongodb """
from pydantic import BaseModel
from typing import Optional


class FileMetadata(BaseModel):
    original_url: str
    product_name: str
    filename: Optional[str] = None
    content_type: Optional[str] = None
    size: Optional[int] = None
