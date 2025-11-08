# app/services/postgres.py
"""
    сервисы создаются для каждой модели <Имя модеоли>Service
    при необходимости методы могут быть перегружены
"""
from app.services.base import Service


class CodeService(Service):
    pass


class NameService(Service):
    pass


class RawService(Service):
    pass


class ImageService(Service):
    pass
