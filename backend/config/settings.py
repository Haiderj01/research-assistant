import os
from dotenv import load_dotenv

load_dotenv()

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve_path(env_key: str, default: str) -> str:
    val = os.getenv(env_key, default)
    if val.startswith("backend/"):
        val = val[len("backend/"):]
    return os.path.join(_BASE_DIR, val)


GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME: str = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME: str = os.getenv(
    "GEMINI_MODEL_NAME",
    "gemini-3.6-flash",
)
JWT_SECRET_KEY: str | None = os.getenv("JWT_SECRET_KEY")
GOOGLE_CLIENT_ID: str | None = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET: str | None = os.getenv("GOOGLE_CLIENT_SECRET")
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
UPLOAD_DIRECTORY: str = _resolve_path("UPLOAD_DIRECTORY", "uploads")
DATABASE_URL: str = os.getenv("DATABASE_URL", "mongodb://localhost:27017/research_assistant")
VECTOR_STORE_PATH: str = _resolve_path("VECTOR_STORE_PATH", "vector_store")
APPLICATION_PORT: int = int(os.getenv("APPLICATION_PORT", "5003"))
DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
LOGGING_LEVEL: str = os.getenv("LOGGING_LEVEL", "INFO").upper()

MAX_FILE_SIZE_MB: int = 50
ALLOWED_EXTENSIONS: set = {".pdf"}
DEFAULT_CHUNK_SIZE: int = 500
DEFAULT_CHUNK_OVERLAP: int = 50
DEFAULT_TOP_K: int = 5
VECTOR_SEARCH_OVERSAMPLE_FACTOR: int = 3
VECTOR_SEARCH_MAX_OVERSAMPLE_FACTOR: int = 32
GAP_MAP_CONCURRENCY: int = int(os.getenv("GAP_MAP_CONCURRENCY", "5"))
MAX_LLM_INPUT_CHARS: int = int(os.getenv("MAX_LLM_INPUT_CHARS", "32000"))
EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"


def validate_required():
    missing = []
    if not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    if not JWT_SECRET_KEY:
        missing.append("JWT_SECRET_KEY")
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"Set them in a .env file or export them before starting the server."
        )