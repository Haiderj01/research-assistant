import pytest
import mongomock
from backend.services.database_service import DatabaseService


@pytest.fixture(autouse=True)
def isolate_database():
    """Force all tests to run against an in-memory mongomock database.

    Prevents the test suite from reading or writing the real MongoDB
    (e.g. a configured Atlas cluster) and keeps every test isolated.
    """
    DatabaseService.disconnect()
    DatabaseService._client = mongomock.MongoClient()
    DatabaseService._db = DatabaseService._client["research_assistant"]
    DatabaseService._ensure_indexes()
    yield
    DatabaseService.disconnect()
