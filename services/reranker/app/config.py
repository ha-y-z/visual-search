from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    RERANKER_MODEL: str = "Qwen/Qwen3-VL-Reranker-2B"
    RERANKER_DEVICE: str = "auto"
    LOG_LEVEL: str = "INFO"


settings = Settings()
