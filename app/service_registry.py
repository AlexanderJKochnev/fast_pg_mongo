# app/service_registry.py
"""  регистрация repo services pydantic models """

_SERVICE_REGISTRY: dict = {}
_REPOSITORY_REGISTRY: dict = {}
_PYSCHEMA_REGISTRY: dict = {}


def register_pyschema(name: str, cls):
    _PYSCHEMA_REGISTRY[name.lower()] = cls


def get_pyschema(name: str):
    return _PYSCHEMA_REGISTRY.get(name.lower())


def get_all_pyschema():
    return _PYSCHEMA_REGISTRY.copy()


def register_repo(name: str, cls):
    _REPOSITORY_REGISTRY[name.lower()] = cls


def get_repo(name: str):
    return _REPOSITORY_REGISTRY.get(name.lower())


def get_all_repo():
    return _REPOSITORY_REGISTRY.copy()


def register_service(name: str, cls):
    _SERVICE_REGISTRY[name.lower()] = cls


def get_service(name: str):
    return _SERVICE_REGISTRY.get(name.lower())


def get_all_services():
    return _SERVICE_REGISTRY.copy()
