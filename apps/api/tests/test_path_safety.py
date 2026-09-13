from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.product_images import product_id_to_path
from app.search.hybrid_search import HybridSearch


def test_product_id_to_path_rejects_traversal(isolated_data_dir):
    from app.config import settings

    settings.HIGH_RES_IMAGE_DIR.mkdir(parents=True)
    assert product_id_to_path("../../etc/passwd") is None


def test_product_id_to_path_rejects_absolute_escape(isolated_data_dir):
    from app.config import settings

    settings.HIGH_RES_IMAGE_DIR.mkdir(parents=True)
    assert product_id_to_path("../../../../etc/shadow") is None


def test_product_id_to_path_accepts_legitimate_id(isolated_data_dir):
    from app.config import settings

    image_dir = settings.HIGH_RES_IMAGE_DIR
    image_dir.mkdir(parents=True)
    (image_dir / "42.jpg").write_bytes(b"fake-jpeg-bytes")

    result = product_id_to_path("42")

    assert result is not None
    assert result.name == "42.jpg"
    assert result.is_relative_to(image_dir.resolve())


def test_product_id_to_path_missing_file_returns_none(isolated_data_dir):
    from app.config import settings

    settings.HIGH_RES_IMAGE_DIR.mkdir(parents=True)
    assert product_id_to_path("does-not-exist") is None


class _StubLexicalSearch:
    def query(self, text_query: str, image_base64: str) -> list[str]:
        return []


class _StubSemanticSearch:
    def text_semantic_search(self, text: str) -> list[str]:
        return []

    def image_semantic_search(self, image_array) -> list[str]:
        return []

    def multimodal_semantic_search(self, text, image_array) -> list[str]:
        return []


class _StubReranker:
    def __init__(self, uris: list[str]):
        self.uris = uris

    def rerank(self, text_query: str, ids: list[str]) -> list[str]:
        return self.uris


def _make_hybrid_search(reranked_uris: list[str]) -> HybridSearch:
    # Bypass __init__ (which loads BM25, SigLIP and the reranker HTTP client) --
    # the path-containment logic under test runs after reranking, so only the
    # reranker's returned URIs matter.
    hs = HybridSearch.__new__(HybridSearch)
    hs.lexical_search = _StubLexicalSearch()
    hs.semantic_search = _StubSemanticSearch()
    hs.reranker = _StubReranker(reranked_uris)
    hs.executor = ThreadPoolExecutor(max_workers=2)
    return hs


def test_hybrid_search_confines_results_to_image_dir(isolated_data_dir):
    from app.config import settings

    image_dir = settings.HIGH_RES_IMAGE_DIR
    image_dir.mkdir(parents=True)

    malicious_uris = [
        "../../etc/passwd",
        "..",
        "../../../../etc/shadow",
        "a/b/../../../outside.jpg",
    ]

    hs = _make_hybrid_search(malicious_uris)
    results = hs.hybrid_search(text_query="shoes")

    resolved_dir = image_dir.resolve()
    for path in results:
        assert Path(path).is_relative_to(resolved_dir)


def test_hybrid_search_returns_benign_results(isolated_data_dir):
    from app.config import settings

    image_dir = settings.HIGH_RES_IMAGE_DIR
    image_dir.mkdir(parents=True)

    hs = _make_hybrid_search(["1.jpg", "2.jpg"])
    results = hs.hybrid_search(text_query="shoes", k=5)

    assert len(results) == 2
    for path in results:
        assert path.startswith(str(image_dir.resolve()))
