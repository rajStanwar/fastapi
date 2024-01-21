from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.utils.config import settings


def get_db() -> AsyncIOMotorDatabase:
    """Get database connection.

    Returns the MongoDB connection using AsyncIOMotorClient.

    Returns:
        AsyncIOMotorDatabase: MongoDB connection
    """
    if settings.testing:
        # Use mock database for testing
        from mongomock_motor import AsyncMongoMockClient
        mock_db: AsyncMongoMockClient = AsyncMongoMockClient().todoDb
        return mock_db
    else:
        # Use real MongoDB connection
        return AsyncIOMotorClient(settings.mongo_uri).todoDb


db = get_db()