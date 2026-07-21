import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    UPLOAD_DIRECTORY: str = os.getenv("UPLOAD_DIRECTORY", "backend/uploads")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mongodb://localhost:27017/research_assistant")
    VECTOR_STORE_PATH: str = os.getenv("VECTOR_STORE_PATH", "backend/vector_store")
    APPLICATION_PORT: int = int(os.getenv("APPLICATION_PORT", "5003"))
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    LOGGING_LEVEL: str = os.getenv("LOGGING_LEVEL", "INFO").upper()

    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: set = {".pdf"}
    DEFAULT_CHUNK_SIZE: int = 500
    DEFAULT_CHUNK_OVERLAP: int = 50
    DEFAULT_TOP_K: int = 5
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    def validate_required(self):
        missing = []
        if not self.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Set them in a .env file or export them before starting the server."
            )


settings = Settings()
