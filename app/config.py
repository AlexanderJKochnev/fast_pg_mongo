# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.utils import get_path_to_root
from pydantic import PostgresDsn
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=get_path_to_root('.env'),
                                      env_file_encoding='utf-8',
                                      extra='ignore')
    """postgres settings"""
    PORT: int = 18091
    API_PORT: int = 8091
    API_HOST: str = '0.0.0.0'
    API_V1_STR: str = "/api/v1"
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    DB_ECHO_LOG: bool
    # probable secirity issue:
    SECRET_KEY: str
    ALGORITHM: str
    """ mongodb settings"""
    MONGODB_CONTAINER_NAME: str
    MONGO_INITDB_ROOT_USERNAME: str
    MONGO_INITDB_ROOT_PASSWORD: str
    MONGO_INITDB_DATABASE: str
    MONGO_DATABASE: str
    MONGO_OUT_PORT: int = 27017
    MONGO_INN_PORT: int = 27017
    MONGO_HOSTNAME: str
    MONGO_EXPRESS_CONTAINER_NAME: str
    ME_CONFIG_MONGODB_ADMINUSERNAME: str
    ME_CONFIG_MONGODB_ADMINPASSWORD: str
    ME_CONFIG_MONGODB_SERVER: str
    ME_CONFIG_BASICAUTH_USERNAME: str
    ME_CONFIG_BASICAUTH_PASSWORD: str
    ME_OUT_PORT: int
    ME_INN_PORT: int
    # IMAGE SIZING в пикселях
    IMAGE_WIDTH: int
    IMAGE_HEIGH: int
    IMAGE_QUALITY: int
    LENGTH_RANDOM_NAME: int
    PAGE_DEFAULT: int
    PAGE_MIN: int
    PAGE_MAX: int
    """ Project Settings """
    DB_ECHO: bool
    PROJECT_NAME: str
    VERSION: str
    DEBUG: bool
    CORS_ALLOWED_ORIGINS: str
    # PAGING
    PAGE_DEFAULT: int = 20
    PAGE_MIN: int = 0
    PAGE_MAX: int = 100
    # AUTHORIZATIOON
    SECRET_KEY: str = 'gV64m9aIzFG4qpgVphvQbPQrtAO0nM-7YwwOvu0XPt5KJOjAy4AfgLkqJXYEt'
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 50
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    BASE_URL: str
    PORT: int

    @property
    def database_url(self) -> Optional[PostgresDsn]:
        """
             возвращает строку подключения postgresql
        """
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
