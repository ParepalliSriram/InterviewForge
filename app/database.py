import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

logger = logging.getLogger("app.database")

class Database:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    def connect_db(cls):
        try:
            logger.info(f"Connecting to MongoDB at: {settings.MONGODB_URI}")
            cls.client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
            cls.db = cls.client[settings.DATABASE_NAME]
            logger.info("Successfully initiated MongoDB connection.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise e

    @classmethod
    def disconnect_db(cls):
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed.")
            cls.client = None
            cls.db = None

def get_db():
    if Database.db is None:
        Database.connect_db()
    return Database.db
