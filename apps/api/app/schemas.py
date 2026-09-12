from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    controller_ready: bool


class SearchResult(BaseModel):
    product_ids: list[str]
    query_image: str | None = None
    query_text: str | None = None


class ChatMessage(BaseModel):
    text: str


class ErrorResponse(BaseModel):
    detail: str
