from pathlib import Path

from app.config import settings


def path_to_product_id(path: str) -> str:
    return Path(path).stem


def paths_to_product_ids(paths: list[str]) -> list[str]:
    return [path_to_product_id(path) for path in paths]


def product_id_to_path(product_id: str) -> Path | None:
    image_dir = settings.HIGH_RES_IMAGE_DIR.resolve()
    candidate = (image_dir / f"{product_id}.jpg").resolve()
    if candidate.is_relative_to(image_dir) and candidate.is_file():
        return candidate
    return None


def product_ids_to_paths(product_ids: list[str]) -> list[str]:
    paths = (product_id_to_path(product_id) for product_id in product_ids)
    return [str(path) for path in paths if path is not None]
