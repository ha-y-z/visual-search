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


class ProductSummary(BaseModel):
    id: str
    productDisplayName: str
    gender: str | None = None
    masterCategory: str | None = None
    subCategory: str | None = None
    articleType: str | None = None
    baseColour: str | None = None
    season: str | None = None
    usage: str | None = None


class ProductListResponse(BaseModel):
    items: list[ProductSummary]
    total: int


class FilterOptions(BaseModel):
    gender: list[str]
    masterCategory: list[str]
    subCategory: list[str]
    articleType: list[str]
    baseColour: list[str]
    season: list[str]
    usage: list[str]
