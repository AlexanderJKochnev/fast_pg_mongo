# Dockerfile
FROM python:3.12-slim
# slim ?
ARG APP_PORT
ARG APP_HOST
ENV APP_PORT=${WEB_PORT}
ENV APP_HOST=${WEB_HOST}

WORKDIR /app
COPY requirements.txt .
ENV PYTHONUNBUFFERED=1
RUN apt-get update && \
    apt-get install -y libmagic-dev && \
    rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app ./app
# COPY alembic.ini .
COPY .env .
EXPOSE $APP_PORT

CMD ["uvicorn", "app.main:app", "--host", "$APP_HOST", "--port", "$APP_PORT", "--reload"]