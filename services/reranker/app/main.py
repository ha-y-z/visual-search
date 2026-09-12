import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.reranker import Reranker
from app.schemas import HealthResponse, RerankRequest, RerankResult

logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Loading reranker model %s", settings.RERANKER_MODEL)
    app.state.reranker = Reranker()
    logger.info("Reranker ready on device %s", app.state.reranker.device)
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", device=app.state.reranker.device)


@app.post("/rerank", response_model=list[RerankResult])
def rerank(request: RerankRequest) -> list[dict[str, int | float | str]]:
    query = request.query.model_dump(exclude_none=True)
    documents = [doc.model_dump() for doc in request.documents]
    return app.state.reranker.rerank(query, documents, top_k=request.top_k)
