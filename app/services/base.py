# app/service/base.py

from abc import ABCMeta
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.service_registry import register_service
from app.repositories.base import Repository, ModelType
from app.utils import parse_unique_violation2


# joint = '. '


class ServiceMeta(ABCMeta):
    """ нужен для регистрации services для того что бы потом обращаться к ним по имени
        если это не нужно, убрать metaclass из базового класса
    """
    def __new__(cls, name, bases, attrs):
        # if not hasattr(cls, '_registry'):
        #     cls._registry = {}

        new_class = super().__new__(cls, name, bases, attrs)
        # Регистрируем сам класс, а не его экземпляр
        if not attrs.get('__abstract__', False):
            key = name.lower().replace('service', '')
            register_service(key, new_class)
            # cls._registry[key] = new_class  # ← Сохраняем класс!
            # print(f"✅ Зарегистрирован сервис: {name} -> ключ: '{key}'")
        return new_class


class Service(metaclass=ServiceMeta):
    """
        Base Service Layer
    """
    __abstract__ = True

    @classmethod
    async def get_or_create(cls, data: ModelType, repository: Type[Repository],
                            model: ModelType, session: Session) -> ModelType:
        """ проверяет существование, при необходимости добавляет. возвращает результат """
        try:
            data_dict = data.model_dump(exclude_unset=True)
            # поиск существующей записи по полному совпадению объектов
            instance = await repository.get_by_fields(data_dict, model, session)
            if instance:
                return instance
            # запись не найдна
            obj = model(**data_dict)
            instance = await repository.create(obj, model, session)
            await session.flush()
            await session.refresh(instance)
            if not instance.id:
                # Если ID все еще None, принудительно коммитим и снова обновляем
                await session.commit()
                await session.refresh(instance)
            return instance
        except IntegrityError as e:
            # поиск по объекту не всегда дает верный результат
            # - могут быть отклонения в необязательных полях ("Превосходный" != "превосходный")
            # -при полном совпадении обязательных, что выбросит ошибку "нарушение уникальности"
            error_msg = str(e)
            await session.rollback()
            filter = parse_unique_violation2(error_msg)  # ищем какие ключи дали нарушение уникальности
            if filter:  # есть поля по которым нарушена интеграция
                # еще раз ищем запись
                existing_instance = await repository.get_by_fields(filter, model, session)
                if existing_instance:   # запись найдена
                    return existing_instance
                else:   # запись не найден и не может быть добавлена
                    raise Exception("запись не может быть добавлена по неивестной причине")
        except Exception as e:
            raise Exception(f"UNKNOWN_ERROR: {str(e)}") from e

    @classmethod
    async def update_or_create(cls,
                               lookup: Dict[str, Any],
                               defaults: Dict[str, Any],
                               repository: Type[Repository], model: ModelType,
                               session: Session) -> ModelType:
        """ ищет запись по lookup и обновляет значениями default,
            если не находит - создает со значениями lookup + default
            замена patch? - нужно сделать схемы
        """
        result = await repository.get_by_obj(lookup, model, session)
        if result:
            id = result['id']
            return await repository.patch(id, defaults, model, session)
        else:
            data = {**lookup, **defaults}
            obj = model(**data)
            return await cls.repository.create(obj, model, session)

    @classmethod
    async def get_all(cls, ater_date: datetime,
                      page: int, page_size: int, repository: Type[Repository], model: ModelType,
                      session: AsyncSession, ) -> List[dict]:
        # Запрос с загрузкой связей и пагинацией
        skip = (page - 1) * page_size
        items, total = await repository.get_all(ater_date, skip, page_size, model, session)
        result = {"items": items,
                  "total": total,
                  "page": page,
                  "page_size": page_size,
                  "has_next": skip + len(items) < total,
                  "has_prev": page > 1}
        return result

    @classmethod
    async def get(cls, after_date: datetime,
                  repository: Type[Repository], model: ModelType,
                  session: AsyncSession,) -> Optional[List[ModelType]]:
        # Запрос с загрузкой связей -  возвращает список
        result = await repository.get(after_date, model, session)
        return result

    @classmethod
    async def get_by_id(
            cls, id: int, repository: Type[Repository],
            model: ModelType, session: AsyncSession) -> Optional[ModelType]:
        """Получение записи по ID"""
        return await repository.get_by_id(id, model, session)

    @classmethod
    async def patch(cls, id: int, data: ModelType,
                    repository: Type[Repository],
                    model: ModelType, session: AsyncSession) -> dict:
        """
        Редактирование записи по ID
        Возвращает dict с результатом операции
        """
        # Получаем существующую запись
        existing_item = await repository.get_by_id(id, model, session)
        if not existing_item:
            return {'success': False, 'message': f'Редактируемая запись {id} не найдена на сервере',
                    'error_type': 'not_found'}

        data_dict = data.model_dump(exclude_unset=True)
        if not data_dict:
            return {'success': False, 'message': 'Нет данных для обновления', 'error_type': 'no_data'}

        # Выполняем обновление
        result = await repository.patch(existing_item, data_dict, session)
        # Обрабатываем результат
        if result == "unique_constraint_violation":
            return {'success': False, 'message': 'Нарушение уникальности: запись с такими данными уже существует',
                    'error_type': 'unique_constraint_violation'}
        elif result == "foreign_key_violation":
            return {'success': False,
                    'message': 'Нарушение ссылочной целостности: указаны несуществующие связанные объекты',
                    'error_type': 'foreign_key_violation'}
        elif isinstance(result, str) and result.startswith(('integrity_error:', 'database_error:')):
            return {'success': False, 'message': f'Ошибка базы данных при обновлении: {result.split(":", 1)[1]}',
                    'error_type': 'database_error'}
        elif isinstance(result, model):
            return {'success': True, 'data': result, 'message': f'Запись {id} успешно обновлена'}
        else:
            return {'success': False, 'message': f'Неизвестная ошибка при обновлении записи {id}',
                    'error_type': 'unknown_error'}

    @classmethod
    async def delete(cls, id: int, model: ModelType, repository: Type[Repository],
                     session: AsyncSession) -> bool:
        instance = await repository.get_by_id(id, model, session)
        if instance:
            result = await repository.delete(instance, session)

            if result == "foreign_key_violation":
                return {'success': False, 'deleted_count': 0,
                        'message': 'Невозможно удалить запись: на неё ссылаются другие объекты'}
            elif isinstance(result, str) and result.startswith(('integrity_error:', 'database_error:')):
                return {'success': False, 'deleted_count': 0,
                        'message': f'Ошибка базы данных при удалении: {result.split(":", 1)[1]}'}
            elif result is True:
                return {'success': True, 'deleted_count': 1, 'message': f'Запись {id} удалена'}
            else:
                return {'success': False, 'deleted_count': 0, 'message': f'Запись {id} обнаружена, но не удалена.'}
        else:
            return {'success': False, 'deleted_count': 0, 'message': f'Запись {id} не найдена'}
