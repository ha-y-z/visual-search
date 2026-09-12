import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    DATA_DIR: Path = BASE_DIR / "data"
    GOOGLE_API_KEY: str = Field(min_length=1)
    RERANKER_URL: str = "http://localhost:8001"
    RERANK_ENABLED: bool = True
    RERANKER_TIMEOUT_SECONDS: float = 10.0
    LOG_LEVEL: str = "INFO"

    @property
    def SQLITE_PATH(self) -> Path:
        return self.DATA_DIR / "sqlite" / "ecommerce_database.sqlite"

    @property
    def CHROMA_PATH(self) -> Path:
        return self.DATA_DIR / "chroma_db"

    @property
    def BM25_INDEX_PATH(self) -> Path:
        return self.DATA_DIR / "bm25_index_products"

    @property
    def IMAGE_DIR(self) -> Path:
        return self.DATA_DIR / "products" / "images"

    @property
    def HIGH_RES_IMAGE_DIR(self) -> Path:
        return self.DATA_DIR / "products" / "high_images" / "images"


settings = Settings()  # type: ignore[call-arg]  # GOOGLE_API_KEY comes from the environment/.env
os.environ.setdefault("GOOGLE_API_KEY", settings.GOOGLE_API_KEY)


def resolve_legacy_data_path(path_str: str) -> Path:
    """The catalog (SQLite rows and the Chroma collection) was built with
    image paths like '../data/products/images/1.jpg', relative to app/
    rather than to whatever the server's CWD happens to be. Re-anchor the
    'data/...' suffix onto settings.DATA_DIR so a DATA_DIR override (e.g. a
    different volume mount in Docker) is actually respected."""
    path = Path(path_str)
    if path.is_absolute():
        return path
    parts = path.parts
    if "data" in parts:
        return (settings.DATA_DIR / Path(*parts[parts.index("data") + 1 :])).resolve()
    return (BASE_DIR / "app" / path).resolve()
