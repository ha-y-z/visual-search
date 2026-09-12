import logging

import httpx

from app.config import settings
from app.database import DatabaseService

logger = logging.getLogger(__name__)


class Reranker:
    def __init__(self):
        self.db = DatabaseService()
        self.client = httpx.Client(timeout=settings.RERANKER_TIMEOUT_SECONDS)

    def create_documents(self, ids: list[str]) -> list[dict[str, str]]:
        documents = []
        metadata_dict = self.db.get_metadata_from_product_ids(ids)
        for image_uri, metadata in metadata_dict.items():
            documents.append({"text": metadata, "image": image_uri})
        return documents

    def rerank(self, text_query: str, image_base64: str, ids: list[str]) -> list[str]:
        documents = self.create_documents(ids)
        unranked = [doc["image"] for doc in documents]

        if not settings.RERANK_ENABLED:
            return unranked

        query: dict[str, str] = {}
        if text_query:
            query["text"] = text_query
        if image_base64:
            query["image"] = f"data:image/jpeg;base64,{image_base64}"

        try:
            response = self.client.post(
                f"{settings.RERANKER_URL}/rerank",
                json={"query": query, "documents": documents},
            )
            response.raise_for_status()
            rankings = response.json()
        except httpx.HTTPError as exc:
            logger.warning("Reranker call failed, returning un-reranked results: %s", exc)
            return unranked

        return [documents[rank["corpus_id"]]["image"] for rank in rankings]
