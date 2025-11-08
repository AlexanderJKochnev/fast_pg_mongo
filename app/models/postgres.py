# app/models/postgres.py
"""
это пример
"""

from app.models.base import Base, Base_at, str_uniq, str_null_index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, String, Text, ForeignKey


class Code(Base, Base_at):
    code = Mapped[str_uniq]
    url = Mapped[str_uniq]
    status = Column(String, default='pending')  # pending, done, error

    names = relationship("Name", back_populates="codes")


class Name(Base, Base_at):
    code_id: Mapped[int] = mapped_column(ForeignKey("codes.id"), nullable=False)
    # ниже устаревший код - результат тот же
    # code_id = Column(String, ForeignKey('codes.id'))
    name = Mapped[str_uniq]
    url = Mapped[str_uniq]
    status = Column(String, default='pending')

    code: Mapped[Code] = relationship(back_populates="names")
    # code_obj = relationship("Code", back_populates="names")
    rawdata: Mapped["Rawdata"] = relationship(back_populates="names")
    # rawdata = relationship("Rawdata", back_populates="name_obj")
    images: Mapped['Image'] = relationship(back_populates="names")
    # images = relationship("Image", back_populates="names")


class Rawdata(Base, Base_at):
    name_id: Mapped[int] = mapped_column(ForeignKey("names.id"), nullable=False)
    # name_id = Column(String, ForeignKey('names.id'))
    body_html = Column(Text)
    names: Mapped[Name] = relationship(back_populates="rawdata")


class Image(Base, Base_at):
    name_id: Mapped[int] = mapped_column(ForeignKey("names.id"), nullable=False)
    file_id = Mapped[str_null_index]  # ID файла в MongoDB
    file_url = Mapped[str_null_index]  # оригинальная ссылка
    names: Mapped[Name] = relationship(back_populates="images")
    # name_obj = relationship("Name", back_populates="images")
