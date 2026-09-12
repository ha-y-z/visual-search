import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app, get_controller
from app.modality import image_processor


class _FakeDB:
    def __init__(self):
        self.known_ids = {"1", "2"}

    def product_exists(self, product_id: str) -> bool:
        return product_id in self.known_ids


class _FakeController:
    def __init__(self):
        self.db = _FakeDB()

    def query(self, text: str | None = None, image_bytes: bytes | None = None) -> dict:
        # Route real bytes through the real (lightweight) validation so the 422
        # paths are exercised genuinely -- only the heavy model/search machinery
        # is faked out here.
        query_image = image_processor.process_bytes_to_base64(image_bytes) if image_bytes else None
        return {
            "uris": ["/data/products/high_images/images/1.jpg"],
            "query_image": query_image,
            "query_text": text,
        }

    def init_agent(self, init_data: dict):
        yield "hello"
        yield {"type": "images", "uris": []}

    def stream_ai(self, text: str):
        yield f"echo: {text}"

    def reset_session(self) -> None:
        pass


@pytest.fixture
def client(monkeypatch, tmp_path):
    from app.config import settings

    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    image_dir = settings.HIGH_RES_IMAGE_DIR
    image_dir.mkdir(parents=True)
    (image_dir / "1.jpg").write_bytes(b"fake-jpeg-bytes")

    fake_controller = _FakeController()
    app.dependency_overrides[get_controller] = lambda: fake_controller
    # Plain TestClient (no `with` block) never runs the lifespan handler, so the
    # real, multi-GB-model Controller() is never constructed.
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def _no_filesystem_paths_leaked(body: str) -> bool:
    return "/data/" not in body


def test_health_before_lifespan_reports_starting(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "starting", "controller_ready": False}


def test_search_text_only_returns_product_ids_not_paths(client: TestClient):
    response = client.post("/api/search", data={"text": "red shoes"})
    assert response.status_code == 200
    body = response.json()
    assert body["product_ids"] == ["1"]
    assert body["query_text"] == "red shoes"
    assert _no_filesystem_paths_leaked(response.text)


def test_search_with_image_upload(client: TestClient):
    img = Image.new("RGB", (10, 10), (255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/api/search",
        files={"image": ("test.png", buf, "image/png")},
    )
    assert response.status_code == 200
    assert _no_filesystem_paths_leaked(response.text)


def test_search_rejects_bad_upload_format(client: TestClient):
    response = client.post(
        "/api/search",
        files={"image": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
    )
    assert response.status_code == 422


def test_search_rejects_oversized_upload(client: TestClient, monkeypatch):
    from app.modality import image_processor

    monkeypatch.setattr(image_processor, "MAX_UPLOAD_BYTES", 10)
    img = Image.new("RGB", (10, 10), (0, 255, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/api/search",
        files={"image": ("test.png", buf, "image/png")},
    )
    assert response.status_code == 422


def test_get_product_image_found(client: TestClient):
    response = client.get("/api/images/1")
    assert response.status_code == 200


def test_get_product_image_not_found_in_db(client: TestClient):
    response = client.get("/api/images/does-not-exist")
    assert response.status_code == 404
    assert _no_filesystem_paths_leaked(response.text)


def test_get_product_image_known_id_missing_file(client: TestClient):
    response = client.get("/api/images/2")  # known to _FakeDB but no file on disk
    assert response.status_code == 404
    assert _no_filesystem_paths_leaked(response.text)


def test_session_reset(client: TestClient):
    response = client.post("/api/session/reset")
    assert response.status_code == 200
    assert response.json() == {"status": "reset"}


def test_chat_init_streams_sse(client: TestClient):
    response = client.post(
        "/api/chat/init",
        json={"product_ids": ["1"], "query_image": None, "query_text": "red shoes"},
    )
    assert response.status_code == 200
    assert "data:" in response.text


def test_chat_streams_sse(client: TestClient):
    response = client.post("/api/chat", json={"text": "hello"})
    assert response.status_code == 200
    assert "echo: hello" in response.text
