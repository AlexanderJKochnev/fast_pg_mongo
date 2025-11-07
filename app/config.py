# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.utils import get_path_to_root


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=get_path_to_root('.env'),
                                      env_file_encoding='utf-8',
                                      extra='ignore')
    # postgres settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    DB_ECHO_LOG: bool
    # probable secirity issue:
    SECRET_KEY: str
    ALGORITHM: str

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


settings = Settings()
