from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from core.config import settings
from core.logger_utils import get_logger

logger = get_logger(__file__)


class MongoDatabaseConnector:
    """Singleton class to connect to MongoDB database."""

    _instance: MongoClient | None = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            try:
                cls._instance = MongoClient(settings.MONGO_DATABASE_URI)
                logger.info(
                    f"Connection to database with uri: {settings.MONGO_DATABASE_URI} successful"
                )
            except ConnectionFailure:
                logger.error(f"Couldn't connect to the database.")
                raise

        return cls._instance

    def get_database(self, database_name: str | None = None):
        assert self._instance, "Database connection not initialized"
        
        # Use provided database name or fall back to settings
        db_name = database_name or settings.MONGO_DATABASE_NAME
        return self._instance[db_name]

    def close(self):
        if self._instance:  
            self._instance.close()
            logger.info("Connected to database has been closed.")


connection = MongoDatabaseConnector()