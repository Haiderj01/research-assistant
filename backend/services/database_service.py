from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import ConnectionFailure
from backend.config.settings import settings
from backend.utils.logger import logger


class DatabaseService:
    """Manages the MongoDB connection and provides collection access."""

    _client: MongoClient = None
    _db = None

    @classmethod
    def connect(cls) -> bool:
        """Establish connection to MongoDB.

        Returns:
            True if connection succeeded, False otherwise.
        """
        if cls._client is not None:
            return True
        try:
            cls._client = MongoClient(
                settings.DATABASE_URL,
                serverSelectionTimeoutMS=3000,
            )
            cls._client.admin.command("ping")
            cls._db = cls._client.get_default_database()
            cls._ensure_indexes()
            logger.info("Connected to MongoDB")
            return True
        except ConnectionFailure:
            logger.warning("MongoDB connection failed — running without database")
            cls._client = None
            cls._db = None
            return False

    @classmethod
    def get_db(cls):
        """Get the database instance, connecting if necessary."""
        if cls._db is None:
            cls.connect()
        return cls._db

    @classmethod
    def get_collection(cls, name: str):
        """Get a collection by name."""
        db = cls.get_db()
        if db is not None:
            return db[name]
        return None

    @classmethod
    def is_connected(cls) -> bool:
        return cls._db is not None

    @classmethod
    def disconnect(cls):
        if cls._client:
            cls._client.close()
        cls._client = None
        cls._db = None

    @classmethod
    def _ensure_indexes(cls):
        if cls._db is None:
            return
        cls._db.papers.create_index([("upload_date", DESCENDING)])
        cls._db.papers.create_index([("status", ASCENDING)])
        cls._db.papers.create_index([("title", TEXT), ("keywords", TEXT)])
        cls._db.chunks.create_index([("paper_id", ASCENDING)])
        cls._db.chunks.create_index([("vector_id", ASCENDING)], unique=True)
        cls._db.conversations.create_index([("updated_at", DESCENDING)])
        cls._db.questions.create_index([("conversation_id", ASCENDING)])
        cls._db.search_history.create_index([("created_at", DESCENDING)])
