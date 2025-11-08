# app/services/base.py
from abc import ABCMeta
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.service_registry import register_service
from app.repositories.base import Repository, ModelType
from app.utils import parse_unique_violation2


class ServiceMeta(ABCMeta):
    """ нужен для регистрации services"""
    
    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        if not attrs.get('__abstract__', False):
            key = name.lower().replace('service', '')
            register_service(key, new_class)
        return new_class


class Service(metaclass = ServiceMeta):
    """
    Base Service Layer
    """
    __abstract__ = True
    repository = Repository
    
    @classmethod
    async def get_or_create(
            cls, data: Any, session: AsyncSession, model: ModelType
            ) -> ModelType:
        """ проверяет существование, при необходимости добавляет. возвращает результат """
        try:
            data_dict = data.model_dump(exclude_unset = True)
            
            # Исключаем поля отношений из поиска
            search_data = {}
            for key, value in data_dict.items():
                if not key.endswith('s'):  # Исключаем отношения (обычно заканчиваются на 's')
                    search_data[key] = value
            
            # поиск существующей записи
            instance = await cls.repository.get_by_fields(search_data, model, session)
            if instance:
                return instance
            
            # запись не найдена - создаем новую
            obj = model(**data_dict)
            instance = await cls.repository.create(obj, session)
            await session.flush()
            await session.refresh(instance)
            
            if not instance.id:
                await session.commit()
                await session.refresh(instance)
            
            return instance
        
        except IntegrityError as e:
            error_msg = str(e)
            await session.rollback()
            filter = parse_unique_violation2(error_msg)
            if filter:
                existing_instance = await cls.repository.get_by_fields(filter, model, session)
                if existing_instance:
                    return existing_instance
                else:
                    raise Exception(f"Integrity error but cannot find existing record: {error_msg}")
            raise Exception(f"Integrity error: {error_msg}")
        
        except Exception as e:
            await session.rollback()
            raise Exception(f"Service error: {str(e)}")
    
    @classmethod
    async def update_or_create(
            cls, lookup: Dict[str, Any], defaults: Dict[str, Any], model: ModelType, session: AsyncSession
            ) -> ModelType:
        """ ищет запись по lookup и обновляет значениями default """
        result = await cls.repository.get_by_fields(lookup, model, session)
        if result:
            return await cls.repository.patch(result, defaults, session)
        else:
            data = {**lookup, **defaults}
            obj = model(**data)
            return await cls.repository.create(obj, session)
    
    @classmethod
    async def get_all(
            cls, after_date: datetime, page: int, page_size: int, model: ModelType, session: AsyncSession
            ) -> Dict[str, Any]:
        """Получение всех записей с пагинацией"""
        skip = (page - 1) * page_size
        items, total = await cls.repository.get_all(after_date, skip, page_size, model, session)
        return {"items": items, "total": total, "page": page, "page_size": page_size,
                "has_next": skip + len(items) < total, "has_prev": page > 1}
    
    @classmethod
    async def get(
            cls, after_date: datetime, model: ModelType, session: AsyncSession
            ) -> List[ModelType]:
        """Получение всех записей без пагинации"""
        return await cls.repository.get(after_date, model, session)
    
    @classmethod
    async def get_by_id(
            cls, id: int, model: ModelType, session: AsyncSession
            ) -> Optional[ModelType]:
        """Получение записи по ID"""
        return await cls.repository.get_by_id(id, model, session)
    
    @classmethod
    async def patch(
            cls, id: int, data: Any, model: ModelType, session: AsyncSession
            ) -> dict:
        """
        Редактирование записи по ID
        """
        existing_item = await cls.repository.get_by_id(id, model, session)
        if not existing_item:
            return {'success': False, 'message': f'Редактируемая запись {id} не найдена', 'error_type': 'not_found'}
        
        data_dict = data.model_dump(exclude_unset = True)
        if not data_dict:
            return {'success': False, 'message': 'Нет данных для обновления', 'error_type': 'no_data'}
        
        result = await cls.repository.patch(existing_item, data_dict, session)
        
        if result == "unique_constraint_violation":
            return {'success': False, 'message': 'Нарушение уникальности', 'error_type': 'unique_constraint_violation'}
        elif result == "foreign_key_violation":
            return {'success': False, 'message': 'Нарушение ссылочной целостности',
                    'error_type': 'foreign_key_violation'}
        elif isinstance(result, str) and result.startswith(('integrity_error:', 'database_error:')):
            return {'success': False, 'message': f'Ошибка базы данных: {result.split(":", 1)[1]}',
                    'error_type': 'database_error'}
        elif isinstance(result, model):
            return {'success': True, 'data': result, 'message': f'Запись {id} успешно обновлена'}
        else:
            return {'success': False, 'message': f'Неизвестная ошибка', 'error_type': 'unknown_error'}
    
    @classmethod
    async def delete(
            cls, id: int, model: ModelType, session: AsyncSession
            ) -> dict:
        """Удаление записи"""
        instance = await cls.repository.get_by_id(id, model, session)
        if instance:
            result = await cls.repository.delete(instance, session)
            
            if result == "foreign_key_violation":
                return {'success': False, 'deleted_count': 0,
                        'message': 'Невозможно удалить запись: на неё ссылаются другие объекты'}
            elif isinstance(result, str) and result.startswith(('integrity_error:', 'database_error:')):
                return {'success': False, 'deleted_count': 0,
                        'message': f'Ошибка базы данных: {result.split(":", 1)[1]}'}
            elif result is True:
                return {'success': True, 'deleted_count': 1, 'message': f'Запись {id} удалена'}
            else:
                return {'success': False, 'deleted_count': 0, 'message': f'Запись {id} обнаружена, но не удалена.'}
        else:
            return {'success': False, 'deleted_count': 0, 'message': f'Запись {id} не найдена'}
    
    @classmethod
    async def get_by_field(
            cls, field_name: str, field_value: Any, session: AsyncSession, model: ModelType
            ) -> List[ModelType]:
        """Поиск записей по полю"""
        result = await cls.repository.get_by_fields({field_name: field_value}, model, session)
        return [result] if result else []
