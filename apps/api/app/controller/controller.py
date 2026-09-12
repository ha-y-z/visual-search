import logging

from app.ai import RAG, Agent, QueryRewriter, SessionManager, model
from app.modality import image_processor
from app.search import HybridSearch

logger = logging.getLogger(__name__)


class Controller:
    def __init__(self):
        self.hybrid_search: HybridSearch = HybridSearch()
        self.db = self.hybrid_search.semantic_search.db
        self.rag: RAG = RAG(self.hybrid_search)
        self.agent: Agent = Agent(model.ASSISTANT_MODEL, model.SUMMARY_MODEL, self.rag)
        self.session_manager: SessionManager = SessionManager()
        self.query_rewriter: QueryRewriter = QueryRewriter(model.REWRITE_MODEL)

    def query(self, text: str | None = None, image_bytes: bytes | None = None):
        if text and not image_bytes:
            text = self.query_rewriter.rewrite_query(text)
            logger.info("Rewritten query: %s", text)
        resized_image_base64 = None
        if image_bytes:
            resized_image_base64 = image_processor.process_bytes_to_base64(image_bytes)

        reranked_result_uris = self.hybrid_search.hybrid_search(
            text or "", resized_image_base64
        )

        return {
            "uris": reranked_result_uris,
            "query_image": resized_image_base64,
            "query_text": text,
        }

    def init_agent(self, init_data: dict):
        retrieved_uris = init_data.get("uris", [])
        query_image = init_data.get("query_image")
        query_text = init_data.get("query_text")

        retrieved_images_base64 = [
            image_processor.resize_base64_image(encoded)
            for encoded in image_processor.convert_image_paths_to_base64(retrieved_uris)
        ]

        # Build message and invoke
        init_message = self.rag.build_init_message(
            query_text, query_image, retrieved_images_base64=retrieved_images_base64
        )

        return self.agent.stream_agent_msg([init_message])

    def invoke_ai(self, text: str) -> dict:
        thread_id = self.session_manager.get_current_session_id()
        return self.agent.invoke_agent_text(text, thread_id=thread_id)

    def stream_ai(self, text: str):
        thread_id = self.session_manager.get_current_session_id()
        return self.agent.stream_agent_text(text, thread_id=thread_id)

    def reset_session(self):
        self.session_manager.replace_new_session_id()
