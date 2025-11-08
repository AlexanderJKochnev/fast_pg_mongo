# app/repositories/base.py
from abc import ABCMeta
from datetime import datetime
from typing import Any, Dict, Optional, Type, Union, TypeVar
from sqlalchemy.orm import DeclarativeMeta
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.service_registry import register_repo

ModelType = TypeVar("ModelType", bound = DeclarativeMeta)


class RepositoryMeta(ABCMeta):
    """ нужен для регистрации repo для того что бы потом обращаться к нему по имени"""
    
    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        if not attrs.get('__abstract__', False):
            key = name.lower().replace('repository', '')
            register_repo(key, new_class)
        return new_class


class Repository(metaclass = RepositoryMeta):
    __abstract__ = True
    
    @classmethod
    def get_query(cls, model: ModelType):
        """
        Переопределяемый метод.
        Возвращает select() с полными selectinload.
        По умолчанию — без связей.
        """
        return select(model)
    
    @classmethod
    async def create(cls, obj: ModelType, session: AsyncSession) -> ModelType:
        """ создание записи """
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj
    
    @classmethod
    async def patch(
            cls, obj: ModelType, data: Dict[str, Any], session: AsyncSession
            ) -> Union[ModelType, str, None]:
        """
        редактирование записи
        """
        try:
            for k, v in data.items():
                if hasattr(obj, k):
                    setattr(obj, k, v)
            await session.commit()
            await session.refresh(obj)
            return obj
        except IntegrityError as e:
            await session.rollback()
            error_str = str(e.orig).lower()
            if 'unique constraint' in error_str or 'duplicate key' in error_str:
                return "unique_constraint_violation"
            elif 'foreign key constraint' in error_str:
                return "foreign_key_violation"
            return f"integrity_error: {error_str}"
        except Exception as e:
            await session.rollback()
            return f"database_error: {str(e)}"
    
    @classmethod
    async def delete(cls, obj: ModelType, session: AsyncSession) -> Union[bool, str]:
        """
        удаление записи
        """
        try:
            await session.delete(obj)
            await session.commit()
            return True
        except IntegrityError as e:
            await session.rollback()
            error_str = str(e.orig)
            if "foreign key constraint" in error_str.lower() or "violates foreign key constraint" in error_str.lower():
                return "foreign_key_violation"
            return f"integrity_error: {error_str}"
        except Exception as e:
            await session.rollback()
            return f"database_error: {str(e)}"
    
    @classmethod
    async def get_by_id(cls, id: int, model: ModelType, session: AsyncSession) -> Optional[ModelType]:
        """
        get one record by id
        """
        stmt = cls.get_query(model).where(model.id == id)
        result = await session.execute(stmt)
        obj = result.scalar_one_or_none()
        return obj
    
    @classmethod
    async def get_by_obj(cls, data: dict, model: Type[ModelType], session: AsyncSession) -> Optional[ModelType]:
        """
        получение instance по совпадению данных
        """
        valid_fields = {key: value for key, value in data.items() if hasattr(model, key)}
        if not valid_fields:
            return None
        stmt = select(model).filter_by(**valid_fields)
        result = await session.execute(stmt)
        item = result.scalar_one_or_none()
        return item
    
    @classmethod
    async def get_all(
            cls, after_date: datetime, skip: int, limit: int, model: ModelType, session: AsyncSession
            ) -> tuple:
        # Запрос с загрузкой связей и пагинацией
        stmt = cls.get_query(model).where(model.updated_at > after_date).offset(skip).limit(limit)
        total = await cls.get_count(after_date, model, session)
        result = await session.execute(stmt)
        items = result.scalars().all()
        return items, total
    
    @classmethod
    async def get(cls, after_date: datetime, model: ModelType, session: AsyncSession) -> list:
        # Запрос с загрузкой связей NO PAGINATION
        stmt = cls.get_query(model).where(model.updated_at > after_date)
        result = await session.execute(stmt)
        items = result.scalars().all()
        return items
    
    @classmethod
    async def get_by_fields(cls, filter: dict, model: ModelType, session: AsyncSession):
        """
        фильтр по нескольким полям
        filter = {<имя поля>: <искомое значение>, ...}, AND
        """
        try:
            # Исключаем поля отношений из фильтра
            valid_fields = {}
            for key, value in filter.items():
                if hasattr(model, key) and not key.endswith('s'):  # Исключаем отношения (обычно заканчиваются на 's')
                    valid_fields[key] = value
            
            if not valid_fields:
                return None
            
            conditions = []
            for key, value in valid_fields.items():
                column = getattr(model, key)
                if value is None:
                    conditions.append(column.is_(None))
                else:
                    conditions.append(column == value)
            
            stmt = select(model).where(and_(*conditions)).limit(1)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        
        except Exception as e:
            # Логируем ошибку, но не прерываем выполнение
            print(f"Warning in get_by_fields: {filter=}, {model.__name__=}, {e}")
            return None
    
    @classmethod
    async def get_count(cls, after_date: datetime, model: ModelType, session: AsyncSession) -> int:
        """ подсчет количества записей после указанной даты"""
        count_stmt = select(func.count()).select_from(model).where(model.updated_at > after_date)
        count_result = await session.execute(count_stmt)
        total = count_result.scalar()
        return total
    
    @classmethod
    async def get_all_count(cls, model: ModelType, session: AsyncSession) -> int:
        """ количество всех записей в таблице """
        count_stmt = select(func.count()).select_from(model)
        result = await session.execute(count_stmt)
        return result.scalar()
