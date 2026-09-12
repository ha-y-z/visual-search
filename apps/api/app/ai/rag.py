import logging
from typing import Any

from langchain.messages import HumanMessage

from app.modality import image_processor
from app.search import HybridSearch

logger = logging.getLogger(__name__)


class RAG:
    def __init__(self, search: HybridSearch):
        self.search = search

    def retrieve_images(self, query: str) -> tuple[list[dict[str, Any]], dict]:
        """
        Searches the product database to retrieve product/item images.

        Do NOT use this tool for general fashion advice, chatting, or styling tips.
        ONLY invoke this tool if the user explicitly requests to search for a product,
        asks to see examples of items to buy, or wants to find specific fashion pieces in the catalog.
        You MUST explain for each item the reason why it was chosen.

        Args:
            query (str): A detailed, self-contained search string. Do NOT just copy the user's latest message. You MUST incorporate past relevant context, constraints, and preferences from previous conversational turns (e.g., if they earlier said 'I like red' and now say 'show me jackets', the query should be 'red jackets').
        """
        logger.info("Searching for images with query: %s", query)
        results = self.search.hybrid_search(query)

        content_text = f"Successfully retrieved {len(results)} images for the query '{query}'. Describe each image and explain why it is relevant to the query."

        metadata = {"uris": results}
        content: list[dict[str, Any]] = []

        text_part = {"type": "text", "text": content_text}
        image_parts: list[dict[str, Any]] = []
        for uri in results:
            encoded = image_processor.convert_image_path_to_base64(uri)
            if encoded is None:
                continue
            resized = image_processor.resize_base64_image(encoded)
            image_parts.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{resized}"},
                }
            )

        content.extend(image_parts)
        content.append(text_part)

        return content, metadata

    def build_init_message(
        self,
        query: str | None,
        image_base64: str | None,
        retrieved_images_base64: list[str],
    ) -> HumanMessage:
        mime_type = "image/jpeg"
        content: list[str | dict[Any, Any]] = []
        if query:
            content.append(
                {
                    "type": "text",
                    "text": "This is the user's query: " + query,
                }
            )
        if image_base64:
            content.append(
                {
                    "type": "image",
                    "base64": image_base64,
                    "mime_type": mime_type,
                }
            )
        if retrieved_images_base64:
            task_text = "You have been provided with multiple images in this message. Do NOT use any tools to search for or retrieve more images."
            task_text += (
                " The first image is the user's reference image for their query. The subsequent images"
                if image_base64
                else " The images"
            )
            task_text += " are matches that have ALREADY been fetched from the database for you. Your task is ONLY to analyze the fetched images and explain for each image why it is a specific match relevant to"
            task_text += " the user's query" if query else ""
            task_text += " and" if query and image_base64 else ""
            task_text += (
                " their reference image. Note: The second image fetched is match #1, the third image fetched is match #2, and so on."
                if image_base64
                else ""
            )
            content.append(
                {
                    "type": "text",
                    "text": task_text,
                }
            )
            for img in retrieved_images_base64:
                content.append(
                    {
                        "type": "image",
                        "base64": img,
                        "mime_type": mime_type,
                    }
                )
        return HumanMessage(content=content)
