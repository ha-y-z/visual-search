import base64
import io

from PIL import Image
from transformers import logging, pipeline

from app.database import DatabaseService

logging.set_verbosity_error()


class ImageTagger:
    def __init__(self):
        checkpoint = "patrickjohncyh/fashion-clip"
        self.classifier = pipeline(
            model=checkpoint, task="zero-shot-image-classification"
        )
        self.product_categories = DatabaseService().get_article_types()

    def tag_image(self, image_base64: str) -> str:
        image_bytes = base64.b64decode(image_base64)
        return self.classifier(
            image=Image.open(io.BytesIO(image_bytes)),
            candidate_labels=self.product_categories,
        )[0]["label"]
