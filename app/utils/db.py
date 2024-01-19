from motor.motor_asyncio import AsyncIOMotorClient
from app.utils.config import settings

db_client = AsyncIOMotorClient(settings.mongo_uri)
db = db_client.todoDb