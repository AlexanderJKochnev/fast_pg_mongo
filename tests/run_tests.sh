#!/bin/bash

# тесты снаружи контейнера
# pytest --ignore=tests/test_postgres.py --ignore=tests/test_mock_db.py --tb=no --disable-warnings -vv
# pytest tests/ --ignore=tests/test_postgres.py --tb=no --disable-warnings -vv
# docker exec -it app pytest tests/test_postgres.py --tb=no --disable-warnings -vv
# pytest -m 'not docker' --tb=no --disable-warnings -vv
pytest tests/test_codes.py \
       tests/test_names.py \
       tests/test_mongodb_crud.py
pytest tests/test_cascade_delete.py
pytest tests/test_cleanup_service.py
pytest tests/test_mongo_files.py
pytest tests/test_cascade_files.py

