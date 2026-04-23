from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MongoDB — replaces MySQL/SQLAlchemy
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "restaurant_platform"

    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    TAVILY_API_KEY: str = ""

    UPLOAD_DIR: str = "uploads"
    FRONTEND_URL: str = "http://localhost:5173"

    # Kafka — leave empty to disable event publishing (app works without Kafka)
    KAFKA_BOOTSTRAP_SERVERS: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
