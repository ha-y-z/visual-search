import torch
from sentence_transformers import CrossEncoder

from app.config import settings

IMAGE_SIZE = 300


def resolve_device(requested: str) -> str:
    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return requested


class Reranker:
    def __init__(self) -> None:
        self.device = resolve_device(settings.RERANKER_DEVICE)
        self.model = CrossEncoder(
            settings.RERANKER_MODEL,
            device=self.device,
            processor_kwargs={"min_pixels": 28 * 28, "max_pixels": IMAGE_SIZE * IMAGE_SIZE},
        )
        if self.device == "cuda":
            self.model.compile()

    def rerank(
        self,
        query: dict[str, str],
        documents: list[dict[str, str]],
        top_k: int | None = None,
    ) -> list[dict[str, int | float | str]]:
        return self.model.rank(query, documents, top_k=top_k)
