import base64
import io
import sqlite3
from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def rgba_png_bytes() -> bytes:
    """An in-memory RGBA PNG, the C1 reproducer (alpha channel breaks a naive JPEG save)."""
    img = Image.new("RGBA", (10, 10), (255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def rgba_png_base64(rgba_png_bytes: bytes) -> str:
    return base64.b64encode(rgba_png_bytes).decode("utf-8")


@pytest.fixture
def isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point settings.DATA_DIR (and everything derived from it) at a throwaway
    directory so tests never touch the real ~15GB data/ tree."""
    from app.config import settings

    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def sqlite_products_db(isolated_data_dir: Path) -> Path:
    from app.config import settings

    sqlite_path = settings.SQLITE_PATH
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(sqlite_path)
    conn.execute(
        """
        CREATE TABLE products (
            id TEXT,
            metadata TEXT,
            image_uri TEXT,
            articleType TEXT,
            high_resolution_image_uri TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO products VALUES (?, ?, ?, ?, ?)",
        ("1", "red shirt", "data/products/images/1.jpg", "Shirts", "data/products/high_images/images/1.jpg"),
    )
    conn.execute(
        "INSERT INTO products VALUES (?, ?, ?, ?, ?)",
        ("2", "blue jeans", "data/products/images/2.jpg", "Jeans", "data/products/high_images/images/2.jpg"),
    )
    conn.commit()
    conn.close()
    return sqlite_path
