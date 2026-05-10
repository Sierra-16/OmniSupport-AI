from pathlib import Path
from pydantic_settings import BaseSettings

_BASE_DIR = Path(__file__).parent.parent
_ENV_FILE = str(_BASE_DIR / ".env")
_CHROMA_DIR = str(_BASE_DIR / "chroma_data")


class Settings(BaseSettings):
    database_url: str = ""
    database_url_sync: str = ""
    redis_url: str = "redis://localhost:6379"
    chroma_persist_dir: str = _CHROMA_DIR
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    llm_api_key: str = ""
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen-plus"
    embedding_model: str = "text-embedding-v2"

    refund_approval_threshold: float = 500.0
    rag_confidence_threshold: float = 0.7

    class Config:
        env_file = _ENV_FILE


settings = Settings()
