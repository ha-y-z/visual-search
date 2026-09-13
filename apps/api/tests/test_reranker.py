import httpx

from app.search.rerank.reranker import Reranker


class _StubDB:
    def __init__(self, metadata_by_uri: dict[str, str]):
        self.metadata_by_uri = metadata_by_uri

    def get_metadata_from_product_ids(self, ids: list[str]) -> dict[str, str]:
        return self.metadata_by_uri


def _make_reranker(metadata_by_uri: dict[str, str]) -> Reranker:
    # Bypass __init__ (which builds a DatabaseService/VectorDatabase and loads
    # the CLIP model) -- rerank() only needs .db and .client.
    reranker = Reranker.__new__(Reranker)
    reranker.db = _StubDB(metadata_by_uri)
    reranker.client = httpx.Client(timeout=1.0)
    return reranker


def test_rerank_disabled_skips_http_call_entirely(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "RERANK_ENABLED", False)
    monkeypatch.setattr(settings, "RERANKER_URL", "http://127.0.0.1:1")  # nothing listens here

    reranker = _make_reranker({"uri-a.jpg": "meta-a", "uri-b.jpg": "meta-b"})

    def _boom(*args, **kwargs):
        raise AssertionError("HTTP call must not happen when RERANK_ENABLED is False")

    monkeypatch.setattr(reranker.client, "post", _boom)

    result = reranker.rerank("shoes", ["a", "b"])

    assert set(result) == {"uri-a.jpg", "uri-b.jpg"}


def test_rerank_degrades_gracefully_when_reranker_unreachable(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "RERANK_ENABLED", True)
    monkeypatch.setattr(settings, "RERANKER_URL", "http://127.0.0.1:1")  # nothing listens here

    reranker = _make_reranker({"uri-a.jpg": "meta-a", "uri-b.jpg": "meta-b"})

    result = reranker.rerank("shoes", ["a", "b"])

    assert set(result) == {"uri-a.jpg", "uri-b.jpg"}


def test_rerank_uses_reranker_response_ordering(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "RERANK_ENABLED", True)

    reranker = _make_reranker({"uri-a.jpg": "meta-a", "uri-b.jpg": "meta-b"})

    class _FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return [{"corpus_id": 1, "score": 0.9}, {"corpus_id": 0, "score": 0.1}]

    monkeypatch.setattr(reranker.client, "post", lambda *a, **k: _FakeResponse())

    result = reranker.rerank("shoes", ["a", "b"])

    assert result == [reranker.create_documents(["a", "b"])[1]["image"], reranker.create_documents(["a", "b"])[0]["image"]]
