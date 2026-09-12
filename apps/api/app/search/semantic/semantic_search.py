import numpy as np

from app.database import DatabaseService


class SemanticSearch:
    def __init__(self):
        self.db: DatabaseService = DatabaseService()
        self.embedding_function = self.db.vector_db.embedding_function

    # https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/02904.pdf
    def calculate_slerp_embedding(
        self, text: str, image_array: np.ndarray, alpha: float = 0.8
    ) -> np.ndarray:
        mixed_embedding = self.embedding_function([text, image_array])  # type: ignore[arg-type]
        text_embedding = mixed_embedding[0] / np.linalg.norm(mixed_embedding[0])
        image_embedding = mixed_embedding[1] / np.linalg.norm(mixed_embedding[1])
        dot = np.clip(np.dot(text_embedding, image_embedding), -1.0, 1.0)
        theta = np.arccos(dot)

        # Identical/parallel embeddings make sin(theta) == 0, which would
        # divide by zero; linear interpolation is the correct SLERP limit there.
        if np.isclose(np.sin(theta), 0.0):
            slerp = (1 - alpha) * image_embedding + alpha * text_embedding
        else:
            slerp = (np.sin((1 - alpha) * theta) / np.sin(theta)) * image_embedding + (
                np.sin(alpha * theta) / np.sin(theta)
            ) * text_embedding

        return np.expand_dims(slerp, axis=0)

    def multimodal_semantic_search(
        self, text: str, image_array: np.ndarray
    ) -> list[str]:
        slerp_embedding = self.calculate_slerp_embedding(text, image_array)

        results = self.db.query_vector_db_embeddings(slerp_embedding)
        return results["ids"][0]

    def text_semantic_search(self, text: str) -> list[str]:
        results = self.db.query_vector_db_text(text)
        return results["ids"][0]

    def image_semantic_search(self, image_array: np.ndarray) -> list[str]:
        results = self.db.query_vector_db_image(image_array)
        return results["ids"][0]
