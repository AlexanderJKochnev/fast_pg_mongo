# app/schemas/postgres.py
"""
    Pydanctic models - для простых случаев - просто скинь slqalchemy модели в LLM
    она тебе за 2 секунды все сделает
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Базовые классы схем
class PaginationBase(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int


# Code схемы
class CodeCreate(BaseModel):
    code: str
    url: str
    status: Optional[str] = 'pending'


class CodeRead(BaseModel):
    id: int
    code: str
    url: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CodePatch(BaseModel):
    code: Optional[str] = None
    url: Optional[str] = None
    status: Optional[str] = None


class CodeDelete(BaseModel):
    id: int


class CodePaginationRead(PaginationBase):
    items: List[CodeRead]


# Name схемы
class NameCreate(BaseModel):
    code_id: int
    name: str
    url: str
    status: Optional[str] = 'pending'


class NameRead(BaseModel):
    id: int
    code_id: int
    name: str
    url: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NamePatch(BaseModel):
    code_id: Optional[int] = None
    name: Optional[str] = None
    url: Optional[str] = None
    status: Optional[str] = None


class NameDelete(BaseModel):
    id: int


class NamePaginationRead(PaginationBase):
    items: List[NameRead]


# Rawdata схемы
class RawdataCreate(BaseModel):
    name_id: int
    body_html: Optional[str] = None


class RawdataRead(BaseModel):
    id: int
    name_id: int
    body_html: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RawdataPatch(BaseModel):
    name_id: Optional[int] = None
    body_html: Optional[str] = None


class RawdataDelete(BaseModel):
    id: int


class RawdataPaginationRead(PaginationBase):
    items: List[RawdataRead]


# Image схемы
class ImageCreate(BaseModel):
    name_id: int
    file_id: Optional[str] = None
    file_url: Optional[str] = None


class ImageRead(BaseModel):
    id: int
    name_id: int
    file_id: Optional[str]
    file_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ImagePatch(BaseModel):
    name_id: Optional[int] = None
    file_id: Optional[str] = None
    file_url: Optional[str] = None


class ImageDelete(BaseModel):
    id: int


class ImagePaginationRead(PaginationBase):
    items: List[ImageRead]
