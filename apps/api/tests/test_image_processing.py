import base64
import io

import pytest
from PIL import Image

from app.modality import image_processor


def test_process_bytes_to_base64_handles_rgba_png(rgba_png_bytes: bytes):
    """C1 reproducer: an alpha-channel PNG used to blow up trying to save as JPEG
    without a .convert('RGB') first."""
    result = image_processor.process_bytes_to_base64(rgba_png_bytes)
    decoded = Image.open(io.BytesIO(base64.b64decode(result)))
    assert decoded.format == "JPEG"
    assert decoded.mode == "RGB"


def test_resize_base64_image_handles_rgba_source(rgba_png_base64: str):
    result = image_processor.resize_base64_image(rgba_png_base64, size=(50, 50))
    decoded = Image.open(io.BytesIO(base64.b64decode(result)))
    assert decoded.format == "JPEG"
    assert decoded.size == (50, 50)


def test_process_bytes_to_base64_rejects_oversized_upload(monkeypatch, rgba_png_bytes: bytes):
    monkeypatch.setattr(image_processor, "MAX_UPLOAD_BYTES", 10)
    with pytest.raises(ValueError, match="exceeds maximum upload size"):
        image_processor.process_bytes_to_base64(rgba_png_bytes)


def test_process_bytes_to_base64_rejects_disallowed_format():
    img = Image.new("RGB", (10, 10), (0, 255, 0))
    buf = io.BytesIO()
    img.save(buf, format="BMP")
    with pytest.raises(ValueError, match="Unsupported image format"):
        image_processor.process_bytes_to_base64(buf.getvalue())


def test_process_bytes_to_base64_accepts_allowed_formats():
    img = Image.new("RGB", (10, 10), (0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    result = image_processor.process_bytes_to_base64(buf.getvalue())
    assert isinstance(result, str)
    assert len(result) > 0


def test_convert_image_path_to_base64_skips_missing_file(tmp_path):
    missing = tmp_path / "does_not_exist.jpg"
    assert image_processor.convert_image_path_to_base64(str(missing)) is None


def test_convert_image_paths_to_base64_skips_only_missing(tmp_path):
    present = tmp_path / "present.jpg"
    Image.new("RGB", (5, 5)).save(present, format="JPEG")
    missing = tmp_path / "missing.jpg"
    results = image_processor.convert_image_paths_to_base64([str(present), str(missing)])
    assert len(results) == 1
