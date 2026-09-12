import logging

import chromadb
import numpy as np
from chromadb.api.types import URI, Image
from chromadb.utils.data_loaders import ImageLoader
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction

from app.config import resolve_legacy_data_path, settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class _CollectionRelativeImageLoader(ImageLoader):
    def _load_image(self, uri: URI | None) -> Image | None:
        if uri is None:
            return None
        return np.array(self._PILImage.open(resolve_legacy_data_path(uri)))


class VectorDatabase:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(settings.CHROMA_PATH))
        self.embedding_function: OpenCLIPEmbeddingFunction = OpenCLIPEmbeddingFunction(
            model_name="hf-hub:Marqo/marqo-fashionSigLIP"
        )
        self.data_loader = _CollectionRelativeImageLoader()
        self.create_collection()

    def create_collection(self):
        self.client.get_or_create_collection(
            name="product_images",
            embedding_function=self.embedding_function,
            data_loader=self.data_loader,
        )

    def delete_collection(self):
        try:
            self.client.delete_collection(name="product_images")
        except Exception as e:
            logger.warning("Collection does not exist, skipping deletion: %s", e)

    def get_collection(self) -> chromadb.Collection:
        return self.client.get_collection(
            name="product_images",
            embedding_function=self.embedding_function,
            data_loader=self.data_loader,
        )

    def query_text(self, text, n_results=5):
        collection: chromadb.Collection = self.get_collection()
        results = collection.query(
            query_texts=[text],
            n_results=n_results,
            include=["data", "embeddings"],
        )
        return results

    def query_embeddings(self, embeddings, n_results=5):
        collection: chromadb.Collection = self.get_collection()
        results = collection.query(
            query_embeddings=embeddings,
            n_results=n_results,
            include=["data"],
        )
        return results

    def query_image(self, image, n_results=5):
        collection: chromadb.Collection = self.get_collection()
        results = collection.query(
            query_images=[image],
            n_results=n_results,
            include=["data", "embeddings"],
        )
        return results
