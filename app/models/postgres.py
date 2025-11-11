# app/models/postgres.py
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List
from app.models.base import Base


class Code(Base):
    __tablename__ = "codes"

    code: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    url: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(50))

    # Relationships
    names: Mapped[List["Name"]] = relationship("Name", back_populates="code", cascade="all, delete-orphan")


class Name(Base):
    __tablename__ = "names"

    code_id: Mapped[int] = mapped_column(ForeignKey("codes.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    url: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(50))

    # Relationships с каскадным удалением
    code: Mapped["Code"] = relationship("Code", back_populates="names")
    raw_data: Mapped[Optional["Rawdata"]] = relationship(
        "Rawdata", back_populates="name", cascade="all, delete-orphan", uselist=False)
    images: Mapped[List["Image"]] = relationship("Image", back_populates="name", cascade="all, delete-orphan")


class Rawdata(Base):
    __tablename__ = "rawdata"

    name_id: Mapped[int] = mapped_column(ForeignKey("names.id", ondelete="CASCADE"), unique=True)
    body_html: Mapped[Optional[str]] = mapped_column(Text)

    name: Mapped["Name"] = relationship("Name", back_populates="raw_data")


class Image(Base):
    __tablename__ = "images"

    name_id: Mapped[int] = mapped_column(ForeignKey("names.id", ondelete="CASCADE"))
    file_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    file_url: Mapped[Optional[str]] = mapped_column(String(255), index=True)

    name: Mapped["Name"] = relationship("Name", back_populates="images")
