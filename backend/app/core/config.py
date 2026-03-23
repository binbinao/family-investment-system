from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/family_invest"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    SESSION_EXPIRE_HOURS: int = 168  # 7 days
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    AI_DAILY_LIMIT: int = 100
    AI_DEEP_MAX_TOKENS: int = 30000

    class Config:
        env_file = ".env"


settings = Settings()
