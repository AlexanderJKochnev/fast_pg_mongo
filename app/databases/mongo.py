# app/databases/mongo.py

from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Depends
from typing import Optional
from app.config import settings


class MongoDB:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None

    async def connect(self, connection_string: str, database_name: str):
        if self.client is None:
            self.client = AsyncIOMotorClient(connection_string)
            self.database = self.client[database_name]

    async def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
            self.database = None


mongodb = MongoDB()


# зависимость client+database для использования в роутах
async def get_mongodb():
    return mongodb


# зависимость только database для использования в роутах
async def get_database(mongodb_instance: MongoDB = Depends(get_mongodb)):
    if mongodb_instance.database is None:
        default_url = settings.mongo_url
        default_db = settings.MONGO_DATABASE
        # default_url = os.getenv("MONGO_URL", "mongodb://admin:admin@localhost:27027")
        # default_db = os.getenv("MONGO_DB", "files_db")
        await mongodb_instance.connect(default_url, default_db)
    return mongodb_instance.database
