from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "FarmGPT"
    debug: bool = True

    # Anthropic
    anthropic_api_key: str = ""

    # Database (optional - not used in cloud free tier)
    database_url: str = ""

    # Redis (optional)
    redis_url: str = ""

    # ChromaDB - local persistent mode for cloud
    chroma_persist_dir: str = "/tmp/chroma_data"

    # CORS (콤마로 여러 도메인 지정 가능)
    cors_origins: str = "http://localhost:3000,https://*.vercel.app"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
