import json
import logging
from collections.abc import AsyncIterator, Generator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from PIL import UnidentifiedImageError

from app.controller import Controller
from app.logging_config import configure_logging
from app.product_images import paths_to_product_ids, product_id_to_path, product_ids_to_paths
from app.schemas import ChatMessage, ErrorResponse, HealthResponse, SearchResult

configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Loading models and building Controller")
    app.state.controller = Controller()
    app.state.controller_ready = True
    logger.info("Controller ready")
    yield
    app.state.controller_ready = False


app = FastAPI(lifespan=lifespan)


def get_controller(request: Request) -> Controller:
    return request.app.state.controller


ControllerDep = Annotated[Controller, Depends(get_controller)]


@app.exception_handler(UnidentifiedImageError)
def handle_unidentified_image(request: Request, exc: UnidentifiedImageError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": "Uploaded file is not a valid image"})


@app.exception_handler(ValueError)
def handle_value_error(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    ready = bool(getattr(request.app.state, "controller_ready", False))
    return HealthResponse(status="ok" if ready else "starting", controller_ready=ready)


@app.post("/api/search", response_model=SearchResult, responses={422: {"model": ErrorResponse}})
def search(
    controller: ControllerDep,
    text: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
) -> SearchResult:
    image_bytes = image.file.read() if image is not None else None
    result = controller.query(text=text, image_bytes=image_bytes)
    return SearchResult(
        product_ids=paths_to_product_ids(result["uris"]),
        query_image=result["query_image"],
        query_text=result["query_text"],
    )


def _sse_event(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def _stream_agent_response(chunks: Generator[Any]) -> Generator[str]:
    for chunk in chunks:
        if isinstance(chunk, str):
            yield _sse_event({"type": "token", "text": chunk})
        else:
            product_ids = paths_to_product_ids(chunk.get("uris", []))
            yield _sse_event({"type": "images", "product_ids": product_ids})


@app.post("/api/chat/init")
def chat_init(search_result: SearchResult, controller: ControllerDep) -> StreamingResponse:
    init_data = {
        "uris": product_ids_to_paths(search_result.product_ids),
        "query_image": search_result.query_image,
        "query_text": search_result.query_text,
    }
    chunks = controller.init_agent(init_data)
    return StreamingResponse(_stream_agent_response(chunks), media_type="text/event-stream")


@app.post("/api/chat")
def chat(message: ChatMessage, controller: ControllerDep) -> StreamingResponse:
    chunks = controller.stream_ai(message.text)
    return StreamingResponse(_stream_agent_response(chunks), media_type="text/event-stream")


@app.post("/api/session/reset")
def reset_session(controller: ControllerDep) -> dict[str, str]:
    controller.reset_session()
    return {"status": "reset"}


@app.get("/api/images/{product_id}", responses={404: {"model": ErrorResponse}})
def get_product_image(product_id: str, controller: ControllerDep) -> FileResponse:
    if not controller.db.product_exists(product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    path = product_id_to_path(product_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path, media_type="image/jpeg")
