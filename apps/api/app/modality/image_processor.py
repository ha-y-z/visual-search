import base64
import io
import logging
from pathlib import Path

import numpy as np
from PIL import Image

IMAGE_CONVERSION_SIZE = 300
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_UPLOAD_FORMATS = {"JPEG", "PNG", "WEBP"}

Image.MAX_IMAGE_PIXELS = 20_000_000

logger = logging.getLogger(__name__)


def convert_image_path_to_base64(image_path: str) -> str | None:
    if not Path(image_path).is_file():
        logger.warning("Image file not found, skipping: %s", image_path)
        return None
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_string


def convert_image_paths_to_base64(image_paths: list[str]) -> list[str]:
    encoded = (convert_image_path_to_base64(path) for path in image_paths)
    return [image for image in encoded if image is not None]


def resize_base64_image(
    base64_string: str, size: tuple = (IMAGE_CONVERSION_SIZE, IMAGE_CONVERSION_SIZE)
) -> str:
    img = Image.open(io.BytesIO(base64.b64decode(base64_string))).convert("RGB")
    resized_image = img.resize(size, Image.Resampling.LANCZOS)
    buffered = io.BytesIO()
    resized_image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def convert_base64_to_image_array(base64_string: str) -> np.ndarray:
    img = Image.open(io.BytesIO(base64.b64decode(base64_string))).convert("RGB")
    resized_image = img.resize(
        (IMAGE_CONVERSION_SIZE, IMAGE_CONVERSION_SIZE), Image.Resampling.LANCZOS
    )
    return np.array(resized_image)


def process_bytes_to_base64(
    image_bytes: bytes, size: tuple = (IMAGE_CONVERSION_SIZE, IMAGE_CONVERSION_SIZE)
) -> str:
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError(f"Image exceeds maximum upload size of {MAX_UPLOAD_BYTES} bytes")
    opened_img = Image.open(io.BytesIO(image_bytes))
    if opened_img.format not in ALLOWED_UPLOAD_FORMATS:
        raise ValueError(f"Unsupported image format: {opened_img.format}")
    img = opened_img.convert("RGB")
    resized_image = img.resize(size, Image.Resampling.LANCZOS)
    buffered = io.BytesIO()
    resized_image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")
