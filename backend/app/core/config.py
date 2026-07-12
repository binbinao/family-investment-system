from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_REPO_ROOT = _BACKEND_DIR.parent

# 已知的不安全默认凭据片段：生产环境出现即拒绝启动
_INSECURE_DB_MARKERS = ("postgres:postgres@", "postgres:changeme@", ":changeme@")


def _normalize_openai_sdk_base_url(url: str) -> str:
    """OpenAI SDK posts to ``{base_url}/chat/completions``; base_url must end with ``/v1``."""
    url = url.strip().rstrip("/")
    if not url:
        return url
    if url.lower().endswith("/v1"):
        return url
    return f"{url}/v1"


class Settings(BaseSettings):
    APP_ENV: str = "development"  # development | production
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/family_invest"
    REDIS_URL: str = "redis://localhost:6379/0"
    SESSION_EXPIRE_HOURS: int = 168  # 7 days
    COOKIE_SECURE: bool = False  # 生产（HTTPS）应置为 true
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

    @model_validator(mode="after")
    def _reject_insecure_production_defaults(self) -> "Settings":
        """生产环境不允许带着已知的默认弱数据库凭据静默启动。"""
        if self.APP_ENV.strip().lower() != "production":
            return self
        db_url = self.DATABASE_URL.lower()
        if any(marker in db_url for marker in _INSECURE_DB_MARKERS):
            raise ValueError(
                "APP_ENV=production 但 DATABASE_URL 仍使用默认弱口令，"
                "请设置强数据库口令后再启动。"
            )
        return self

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
