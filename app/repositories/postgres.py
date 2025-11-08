# app/repositories/postgres.py
"""
    репозитории создаютсяя для каждой модели <Имя модеоли>Repository
    при необходимости методы могут быть перегружены
"""
from app.repositories.base import Repository


class CodeRepository(Repository):
    pass


class NameRepository(Repository):
    pass


class RawRepository(Repository):
    pass


class ImageRepository(Repository):
    pass
