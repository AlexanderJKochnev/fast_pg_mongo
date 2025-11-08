# app/models/postgres.py
from app.models.base import Base, Base_at, str_uniq, str_null_index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey
from typing import List, Optional


class Code(Base, Base_at):
    __tablename__ = "codes"
    
    code: Mapped[str] = mapped_column(String(255), unique = True, nullable = False, index = True)
    url: Mapped[str] = mapped_column(String(255), unique = True, nullable = False, index = True)
    status: Mapped[str] = mapped_column(String(50), default = 'pending')  # pending, done, error
    
    # Один Code ко многим Name
    names: Mapped[List["Name"]] = relationship("Name", back_populates = "code", cascade = "all, delete-orphan")


class Name(Base, Base_at):
    __tablename__ = "names"
    
    code_id: Mapped[int] = mapped_column(ForeignKey("codes.id"), nullable = False)
    name: Mapped[str] = mapped_column(String(255), unique = True, nullable = False, index = True)
    url: Mapped[str] = mapped_column(String(255), unique = True, nullable = False, index = True)
    status: Mapped[str] = mapped_column(String(50), default = 'pending')
    
    # Многие Name к одному Code
    code: Mapped["Code"] = relationship("Code", back_populates = "names")
    
    # Один Name к одному Rawdata
    rawdata: Mapped[Optional["Rawdata"]] = relationship("Rawdata", back_populates = "name", uselist = False)
    
    # Один Name ко многим Image
    images: Mapped[List["Image"]] = relationship("Image", back_populates = "name", cascade = "all, delete-orphan")


class Rawdata(Base, Base_at):
    __tablename__ = "rawdata"
    
    name_id: Mapped[int] = mapped_column(ForeignKey("names.id"), nullable = False, unique = True)
    body_html: Mapped[Optional[str]] = mapped_column(Text)
    
    # Один Rawdata к одному Name
    name: Mapped["Name"] = relationship("Name", back_populates = "rawdata")


class Image(Base, Base_at):
    __tablename__ = "images"
    
    name_id: Mapped[int] = mapped_column(ForeignKey("names.id"), nullable = False)
    file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable = True, index = True)  # ID файла в MongoDB
    file_url: Mapped[Optional[str]] = mapped_column(String(255), nullable = True, index = True)  # оригинальная ссылка
    
    # Многие Image к одному Name
    name: Mapped["Name"] = relationship("Name", back_populates = "images")