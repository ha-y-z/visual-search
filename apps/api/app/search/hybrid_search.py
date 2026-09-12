import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.config import settings
from app.modality import image_processor
from app.search.lexical.lexical_search import LexicalSearch
from app.search.rerank.reranker import Reranker
from app.search.semantic.semantic_search import SemanticSearch
from app.timing import timed_stage

logger = logging.getLogger(__name__)


class HybridSearch:
    def __init__(self):
        self.lexical_search = LexicalSearch()
        self.semantic_search = SemanticSearch()
        self.reranker = Reranker()
        # Each call only ever submits 2 tasks (lexical + semantic); a fixed pool
        # built once avoids spinning up an unbounded-default ThreadPoolExecutor
        # per request.
        self.executor = ThreadPoolExecutor(max_workers=2)

    def hybrid_search(
        self, text_query: str = "", image_base64: str | None = None, k: int = 5
    ) -> list[str]:
        result_ids = []

        def run_semantic_search():
            if image_base64:
                image_array = image_processor.convert_base64_to_image_array(image_base64)
                if text_query:
                    return self.semantic_search.multimodal_semantic_search(
                        text_query, image_array
                    )
                else:
                    return self.semantic_search.image_semantic_search(image_array)
            else:
                return self.semantic_search.text_semantic_search(text_query)

        future_lexical = self.executor.submit(
            lambda: self.lexical_search.query(text_query or "", image_base64 or "")
        )
        future_semantic = self.executor.submit(run_semantic_search)

        with timed_stage(logger, "lexical search"):
            lexical_results = future_lexical.result()
        with timed_stage(logger, "semantic search"):
            semantic_results = future_semantic.result()

        result_ids.extend(lexical_results)
        logger.debug("Lexical search returned %s", lexical_results)
        result_ids.extend(semantic_results)
        logger.debug("Semantic search returned %s", semantic_results)

        unique_result_ids = list(set(result_ids))

        with timed_stage(logger, "rerank"):
            reranked_result_uris: list[str] = self.reranker.rerank(
                text_query or "", image_base64 or "", unique_result_ids
            )

        image_dir = settings.HIGH_RES_IMAGE_DIR.resolve()
        resolved_paths = []
        for uri in reranked_result_uris:
            candidate = (image_dir / Path(uri).name).resolve()
            if candidate.is_relative_to(image_dir):
                resolved_paths.append(str(candidate))
        return resolved_paths[:k]
