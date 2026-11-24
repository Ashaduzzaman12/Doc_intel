from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://docintel:docintel@db:5432/docintel"
    redis_url: str = "redis://redis:6379/0"
    ollama_url: str = "http://ollama:11434"
    ollama_model: str = "qwen2.5:7b"
    upload_dir: str = "/app/storage"
    max_upload_mb: int = 100
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
