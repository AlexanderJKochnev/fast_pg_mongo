# app/main.py
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.routers import CodeRouter, NameRouter, RawdataRouter, ImageRouter
from app.databases.postgres import init_db, get_db, engine
from app.databases.mongo import get_mongodb
from app.routers.mongo_file_router import mongo_file_router
from app.routers.cascade_file_router import cascade_file_router


app = FastAPI()

# Инициализация роутеров
code_router = CodeRouter()
name_router = NameRouter()
rawdata_router = RawdataRouter()
image_router = ImageRouter()

# Подключение роутеров
app.include_router(code_router.router)
app.include_router(name_router.router)
app.include_router(rawdata_router.router)
app.include_router(image_router.router)
app.include_router(mongo_file_router)
app.include_router(cascade_file_router)


@app.on_event("startup")
async def startup_event():
    """Создание таблиц при запуске приложения"""
    print("🚀 Запуск приложения...")
    await init_db()


@app.get("/")
async def root():
    return {"message": "API работает"}


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Проверка здоровья с подключением к БД"""
    try:
        # Простой запрос для проверки подключения
        _ = await db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


@app.on_event("shutdown")
async def shutdown_event():
    mongodb_instance = await get_mongodb()
    await mongodb_instance.disconnect()
    await engine.dispose()
