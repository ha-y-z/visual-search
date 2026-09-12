import bm25s

from app.config import settings

from .image_tagger import ImageTagger


class LexicalSearch:
    def __init__(self):
        self.retriever = bm25s.BM25.load(
            str(settings.BM25_INDEX_PATH), load_corpus=True
        )
        self.image_tagger = ImageTagger()

    def search(self, query: str, top_k: int = 5):
        tokenized_query = bm25s.tokenize(query)
        results, scores = self.retriever.retrieve(tokenized_query, k=top_k)
        return results

    def query(self, text_query: str = "", image_base64: str = ""):
        if image_base64:
            tag = self.image_tagger.tag_image(image_base64=image_base64)
            text_query += " " + tag
        results = self.search(text_query.strip())
        return [doc["text"] for doc in results[0]]
