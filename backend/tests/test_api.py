import io
import shutil
import logging

import pytest

from httpx import AsyncClient, ASGITransport

pytestmark = pytest.mark.asyncio

logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger("hidconverter")


@pytest.fixture(autouse=True)
def clean_uploads():
    from backend.main import UPLOAD_DIR
    yield
    if UPLOAD_DIR.exists():
        for item in UPLOAD_DIR.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink(missing_ok=True)


@pytest.fixture
async def client():
    from backend.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_read_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert "<html" in response.text


async def test_get_formats(client: AsyncClient):
    response = await client.get("/api/formats")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    for key in ("image", "audio", "video", "document", "data"):
        assert key in data, f"Missing format category: {key}"
        assert isinstance(data[key], dict)


async def test_get_categories(client: AsyncClient):
    response = await client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "image" in data


async def test_convert_invalid_format(client: AsyncClient):
    png_bytes = _make_test_png()
    files = {"files": ("test.png", png_bytes, "image/png")}
    data = {"target_format": "xyz"}

    response = await client.post("/api/convert", files=files, data=data)
    assert response.status_code in (400, 422)
    body = response.json()
    assert "error" in body or "detail" in body


async def test_convert_png_to_jpg(client: AsyncClient):
    png_bytes = _make_test_png()
    files = {"files": ("test.png", png_bytes, "image/png")}
    data = {"target_format": "jpg", "quality": "85"}

    response = await client.post("/api/convert", files=files, data=data)
    assert response.status_code == 200
    assert response.headers.get("content-type") in (
        "application/octet-stream",
        "image/jpeg",
    )
    assert len(response.content) > 0


async def test_convert_single_file_zip(client: AsyncClient):
    png_bytes = _make_test_png()
    jpg_bytes = _make_test_jpg()

    files = [
        ("files", ("a.png", png_bytes, "image/png")),
        ("files", ("b.jpg", jpg_bytes, "image/jpeg")),
    ]
    data = {"target_format": "webp"}

    response = await client.post("/api/convert", files=files, data=data)
    assert response.status_code == 200
    assert response.headers.get("content-type") in (
        "application/octet-stream",
        "application/zip",
    )
    assert len(response.content) > 0


async def test_hash_file(client: AsyncClient):
    files = {"file": ("data.bin", b"hello world", "application/octet-stream")}
    response = await client.post("/api/hash", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["md5"] == "5eb63bbbe01eeed093cb22bb8f5acdc3"


async def test_hash_text(client: AsyncClient):
    data = {"text": "hello world"}
    response = await client.post("/api/hash", data=data)
    assert response.status_code == 200
    body = response.json()
    assert body["md5"] == "5eb63bbbe01eeed093cb22bb8f5acdc3"


async def test_hash_empty(client: AsyncClient):
    response = await client.post("/api/hash")
    assert response.status_code == 400
    body = response.json()
    assert "error" in body or "detail" in body


async def test_qr_pipeline(client: AsyncClient):
    from backend.converters.qr_converter import pyzbar_decode, qrcode

    if qrcode is None:
        pytest.skip("qrcode library not installed")

    original_text = "https://example.com/hidconverter"

    data = {"text": original_text, "fmt": "png"}
    response = await client.post("/api/qr/encode", data=data)
    assert response.status_code == 200
    assert response.headers.get("content-type") in (
        "image/png",
        "application/octet-stream",
    )
    qr_bytes = response.content
    assert len(qr_bytes) > 100

    if pyzbar_decode is None:
        pytest.skip("pyzbar not available — QR decode skipped")

    files = {"file": ("qrcode.png", qr_bytes, "image/png")}
    response = await client.post("/api/qr/decode", files=files)
    assert response.status_code == 200
    body = response.json()
    decoded = body.get("text", "")
    assert decoded.strip() == original_text


async def test_qr_encode_svg(client: AsyncClient):
    from backend.converters.qr_converter import qrcode

    if qrcode is None:
        pytest.skip("qrcode library not installed")

    data = {"text": "Hello SVG", "fmt": "svg"}
    response = await client.post("/api/qr/encode", data=data)
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    assert "svg" in content_type or "octet-stream" in content_type
    assert b"<svg" in response.content


async def test_qr_decode_invalid_image(client: AsyncClient):
    from backend.converters.qr_converter import pyzbar_decode

    if pyzbar_decode is None:
        pytest.skip("pyzbar not available — QR decode skipped")

    buf = io.BytesIO()
    from PIL import Image
    img = Image.new("RGB", (50, 50), color="blue")
    img.save(buf, "PNG")
    buf.seek(0)

    files = {"file": ("blank.png", buf.getvalue(), "image/png")}
    response = await client.post("/api/qr/decode", files=files)
    assert response.status_code == 422
    body = response.json()
    assert "error" in body or "detail" in body


async def test_metadata_clean(client: AsyncClient):
    png_bytes = _make_test_png()
    files = {"file": ("test.png", png_bytes, "image/png")}
    response = await client.post("/api/metadata/clean", files=files)
    assert response.status_code == 200
    assert len(response.content) > 0


async def test_convert_url_missing(client: AsyncClient):
    data = {"target_format": "jpg"}
    response = await client.post("/api/convert-url", data=data)
    assert response.status_code in (400, 422)
    body = response.json()
    assert "error" in body or "detail" in body


async def test_global_exception_handler(client: AsyncClient):
    response = await client.post("/api/convert")
    assert response.status_code in (400, 422)
    body = response.json()
    assert "error" in body or "detail" in body


# ─── Edge cases ─────────────────────────────────────────────────────────────

async def test_convert_empty_file(client: AsyncClient):
    data = {"target_format": "jpg"}
    files = {"files": ("empty.png", b"", "image/png")}
    response = await client.post("/api/convert", files=files, data=data)
    assert response.status_code in (400, 422)
    body = response.json()
    assert "error" in body or "detail" in body


async def test_convert_corrupted_image(client: AsyncClient):
    data = {"target_format": "jpg"}
    files = {"files": ("corrupt.png", b"not-a-real-png-file", "image/png")}
    response = await client.post("/api/convert", files=files, data=data)
    assert response.status_code in (400, 422, 500)
    body = response.json()
    assert "error" in body or "detail" in body


async def test_convert_filename_with_path_traversal(client: AsyncClient):
    png_bytes = _make_test_png()
    files = {"files": ("../../etc/passwd.png", png_bytes, "image/png")}
    data = {"target_format": "jpg"}
    response = await client.post("/api/convert", files=files, data=data)
    assert response.status_code == 200
    assert len(response.content) > 0


async def test_content_type_single_file(client: AsyncClient):
    png_bytes = _make_test_png()
    files = {"files": ("test.png", png_bytes, "image/png")}
    data = {"target_format": "jpg", "quality": "85"}
    response = await client.post("/api/convert", files=files, data=data)
    assert response.status_code == 200
    ct = response.headers.get("content-type", "")
    assert "jpeg" in ct or "octet-stream" in ct


async def test_qr_encode_empty_text(client: AsyncClient):
    from backend.converters.qr_converter import qrcode
    if qrcode is None:
        pytest.skip("qrcode library not installed")
    data = {"text": "", "fmt": "png"}
    response = await client.post("/api/qr/encode", data=data)
    assert response.status_code in (200, 422)


async def test_large_file_rejection(client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("backend.utils.MAX_FILE_SIZE_BYTES", 100)
    large = b"x" * 101
    files = {"files": ("big.txt", large, "text/plain")}
    data = {"target_format": "pdf"}
    response = await client.post("/api/convert", files=files, data=data)
    assert response.status_code == 413


def _make_test_png() -> bytes:
    from PIL import Image
    buf = io.BytesIO()
    img = Image.new("RGB", (5, 5), color="red")
    img.save(buf, "PNG")
    return buf.getvalue()


def _make_test_jpg() -> bytes:
    from PIL import Image
    buf = io.BytesIO()
    img = Image.new("RGB", (5, 5), color="blue")
    img.save(buf, "JPEG")
    return buf.getvalue()
