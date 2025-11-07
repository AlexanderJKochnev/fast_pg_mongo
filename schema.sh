#!/bin/bash

touch docker-compose.yml Dockerfile requirements.txt .env .flake8 .gitignore .dockerignore
mkdir -p app/schemas app/models app/services app/repositories tests app/databases &&
touch tests/conftest.py
cd app &&
touch __init__.py config.py main.py utils.py &&
cd models &&
touch __init__.py postgres.py mongo.py base.py &&
cd .. && cd schemas
touch __init__.py postgres.py mongo.py base.py &&
cd .. && cd services
touch __init__.py postgres.py mongo.py base.py &&
cd .. && cd repositories
touch __init__.py postgres.py mongo.py base.py &&
cd .. && cd databases
touch __init__.py postgres.py mongo.py