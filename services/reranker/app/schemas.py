from pydantic import BaseModel


class RerankQuery(BaseModel):
    text: str | None = None
    image: str | None = None


class RerankDocument(BaseModel):
    text: str
    image: str


class RerankRequest(BaseModel):
    query: RerankQuery
    documents: list[RerankDocument]
    top_k: int | None = None


class RerankResult(BaseModel):
    corpus_id: int
    score: float


class HealthResponse(BaseModel):
    status: str
    device: str
