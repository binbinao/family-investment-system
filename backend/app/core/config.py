from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_REPO_ROOT = _BACKEND_DIR.parent


def _normalize_openai_sdk_base_url(url: str) -> str:
    """OpenAI SDK posts to ``{base_url}/chat/completions``; base_url must end with ``/v1``."""
    url = url.strip().rstrip("/")
    if not url:
        return url
    if url.lower().endswith("/v1"):
        return url
    return f"{url}/v1"


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/family_invest"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    SESSION_EXPIRE_HOURS: int = 168  # 7 days
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # 官方 DeepSeek（或仅填官方 key、base 走默认）
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # 第三方 DeepSeek 兼容网关（OpenAI SDK 格式）；任一非空则优先于上方官方配置
    DEEPSEEK_VENDOR_API_KEY: str = ""
    DEEPSEEK_VENDOR_BASE_URL: str = ""
    DEEPSEEK_VENDOR_MODEL: str = ""

    AI_DAILY_LIMIT: int = 100
    AI_DEEP_MAX_TOKENS: int = 30000

    model_config = SettingsConfigDict(
        env_file=(
            str(_REPO_ROOT / ".env"),
            str(_BACKEND_DIR / ".env"),
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def resolved_llm_api_key(self) -> str:
        key = (self.DEEPSEEK_VENDOR_API_KEY or self.DEEPSEEK_API_KEY).strip()
        return key

    def resolved_llm_base_url(self) -> str:
        url = (self.DEEPSEEK_VENDOR_BASE_URL or self.DEEPSEEK_BASE_URL).strip()
        return _normalize_openai_sdk_base_url(url)

    def resolved_llm_model(self) -> str:
        model = (self.DEEPSEEK_VENDOR_MODEL or self.DEEPSEEK_MODEL).strip()
        return model


settings = Settings()
