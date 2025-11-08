# app/models/base.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, String, func
from datetime import datetime, timezone


class Base(DeclarativeBase):
    pass


class Base_at:
    """Базовый класс с общими полями"""
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now(),
                                                 onupdate=datetime.now(timezone.utc),
                                                 index=True)


# Типы для полей (теперь это просто аннотации типов)
str_uniq = String(255)
str_null_index = String(255)
