import os
import io
import json
import logging
import uuid
import zipfile
from pathlib import Path
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.converters import (
    ImageConverter, AudioConverter, VideoConverter,
    DocumentConverter, DataConverter, HashConverter,
    encode_qr, decode_qr, clean_metadata,
    download_from_url, download_youtube_audio,
)
from backend.utils import (
    validate_file_size, validate_extension, get_category,
    cleanup_uploads, MAX_FILE_SIZE_BYTES,
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("hidconverter")

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

converters = {
    "image": ImageConverter(),
    "audio": AudioConverter(),
    "video": VideoConverter(),
    "document": DocumentConverter(),
    "data": DataConverter(),
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("HidConverter started")
    cleanup_uploads(str(UPLOAD_DIR))
    yield
    cleanup_uploads(str(UPLOAD_DIR))
    logger.info("HidConverter stopped")


app = FastAPI(
    title="HidConverter",
    description="Universal file conversion API",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    return (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/api/formats")
async def get_formats():
    result = {}
    for category, converter in converters.items():
        result[category] = converter.supported_conversions()
    return result


@app.get("/api/categories")
async def get_categories():
    from backend.utils import FILE_CATEGORIES
    return FILE_CATEGORIES


async def _convert_single(file: UploadFile, target_format: str, job_dir: Path,
                          quality: Optional[int] = None,
                          bitrate: Optional[str] = None,
                          clean_meta: bool = False) -> str:
    ext = os.path.splitext(file.filename or "")[1].lstrip(".").lower()
    logger.info(f"Converting: {file.filename} (.{ext}) -> {target_format}")

    if not validate_extension(ext):
        raise HTTPException(status_code=400, detail=f"Unsupported extension: .{ext}")

    contents = await file.read()
    if not validate_file_size(len(contents)):
        raise HTTPException(status_code=413, detail=f"File too large. Max: {MAX_FILE_SIZE_BYTES // (1024*1024)} MB")

    category = get_category(ext)
    converter = converters.get(category)
    if not converter:
        raise HTTPException(status_code=400, detail=f"No converter for category: {category}")

    conv_map = converter.supported_conversions()
    if ext not in conv_map or target_format not in conv_map[ext]:
        raise HTTPException(status_code=400, detail=f"Conversion .{ext} -> .{target_format} not supported")

    input_path = job_dir / f"input.{ext}"
    with open(input_path, "wb") as f:
        f.write(contents)

    if clean_meta and category == "image":
        logger.info(f"Stripping metadata from {input_path}")
        try:
            clean_metadata(str(input_path), str(input_path))
        except Exception as e:
            logger.warning(f"Metadata cleaning failed (continuing): {e}")

    kwargs = {}
    if quality is not None:
        kwargs["quality"] = quality
    if bitrate is not None:
        kwargs["bitrate"] = bitrate

    try:
        return converter.convert(str(input_path), target_format, str(job_dir), **kwargs)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Ошибка в данных: {e}")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Ошибка конвертации: {e}")


@app.post("/api/convert")
async def convert_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    target_format: str = Form(...),
    quality: Optional[int] = Form(None),
    bitrate: Optional[str] = Form(None),
    clean_meta: bool = Form(False),
):
    job_id = uuid.uuid4().hex
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    background_tasks.add_task(cleanup_uploads, str(UPLOAD_DIR))

    if len(files) == 1:
        output_path = await _convert_single(files[0], target_format, job_dir, quality, bitrate, clean_meta)
        out_name = os.path.basename(output_path)
        return FileResponse(output_path, filename=out_name, media_type="application/octet-stream")

    zip_buffer = io.BytesIO()
    used_names = set()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            try:
                output_path = await _convert_single(file, target_format, job_dir, quality, bitrate, clean_meta)
                base = os.path.basename(output_path)
                stem, ext = os.path.splitext(base)
                arcname = base
                counter = 1
                while arcname in used_names:
                    arcname = f"{stem}_{counter}{ext}"
                    counter += 1
                used_names.add(arcname)
                zf.write(output_path, arcname=arcname)
            except HTTPException as e:
                logger.warning(f"Skipping {file.filename}: {e.detail}")
                continue

    zip_buffer.seek(0)
    zip_path = job_dir / "converted.zip"
    with open(zip_path, "wb") as f:
        f.write(zip_buffer.getvalue())

    return FileResponse(zip_path, filename="converted.zip", media_type="application/zip")


@app.post("/api/convert-url")
async def convert_url(
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    target_format: str = Form(...),
    quality: Optional[int] = Form(None),
    bitrate: Optional[str] = Form(None),
    clean_meta: bool = Form(False),
):
    logger.info(f"URL convert: {url} -> {target_format}")

    job_id = uuid.uuid4().hex
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    background_tasks.add_task(cleanup_uploads, str(UPLOAD_DIR))

    try:
        downloaded_path = download_from_url(url, str(job_dir))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    ext = os.path.splitext(downloaded_path)[1].lstrip(".").lower()
    category = get_category(ext)

    if not category or category == "unknown":
        raise HTTPException(status_code=400, detail=f"Cannot determine file type from: {downloaded_path}")

    audio_exts = {"mp3", "wav", "ogg", "flac", "m4a", "aac"}
    is_audio_target = target_format in audio_exts
    is_youtube = "youtube" in url.lower() or "youtu.be" in url.lower()

    if is_youtube and is_audio_target:
        try:
            output_path = download_youtube_audio(url, str(job_dir), target_format)
            out_name = os.path.basename(output_path)
            return FileResponse(output_path, filename=out_name, media_type="application/octet-stream")
        except RuntimeError as e:
            raise HTTPException(status_code=422, detail=str(e))

    converter = converters.get(category)
    if not converter:
        raise HTTPException(status_code=400, detail=f"No converter for category: {category}")

    conv_map = converter.supported_conversions()
    if ext not in conv_map or target_format not in conv_map[ext]:
        raise HTTPException(status_code=400, detail=f"Conversion .{ext} -> .{target_format} not supported")

    if clean_meta and category == "image":
        try:
            clean_metadata(downloaded_path, downloaded_path)
        except Exception as e:
            logger.warning(f"Metadata cleaning failed (continuing): {e}")

    kwargs = {}
    if quality is not None:
        kwargs["quality"] = quality
    if bitrate is not None:
        kwargs["bitrate"] = bitrate

    try:
        output_path = converter.convert(downloaded_path, target_format, str(job_dir), **kwargs)
        out_name = os.path.basename(output_path)
        return FileResponse(output_path, filename=out_name, media_type="application/octet-stream")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Ошибка в данных: {e}")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Ошибка конвертации: {e}")


@app.post("/api/hash")
async def hash_file(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
):
    if file:
        contents = await file.read()
        if not validate_file_size(len(contents)):
            raise HTTPException(status_code=413, detail="File too large")
        data = contents
        source = file.filename
    elif text:
        data = text.encode("utf-8")
        source = "text"
    else:
        raise HTTPException(status_code=400, detail="Provide a file or text")

    import hashlib
    result = {
        "source": source,
        "md5": hashlib.md5(data).hexdigest(),
        "sha1": hashlib.sha1(data).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    return JSONResponse(content=result)


@app.post("/api/qr/encode")
async def qr_encode(
    text: str = Form(...),
    fmt: str = Form("png"),
):
    job_id = uuid.uuid4().hex
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    if fmt not in ("png", "svg"):
        fmt = "png"

    out_path = os.path.join(str(job_dir), f"qrcode.{fmt}")

    try:
        encode_qr(text, out_path, fmt)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"QR generation failed: {e}")

    media_map = {"png": "image/png", "svg": "image/svg+xml"}
    return FileResponse(out_path, filename=f"qrcode.{fmt}", media_type=media_map.get(fmt, "application/octet-stream"))


@app.post("/api/qr/decode")
async def qr_decode(
    file: UploadFile = File(...),
):
    contents = await file.read()
    if not validate_file_size(len(contents)):
        raise HTTPException(status_code=413, detail="File too large")

    job_id = uuid.uuid4().hex
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    ext = os.path.splitext(file.filename or "image.png")[1].lower()
    input_path = os.path.join(str(job_dir), f"qr_input{ext}")
    with open(input_path, "wb") as f:
        f.write(contents)

    try:
        decoded = decode_qr(input_path)
        return JSONResponse(content={"text": decoded})
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"QR decode failed: {e}")


@app.post("/api/metadata/clean")
async def metadata_clean(
    file: UploadFile = File(...),
):
    contents = await file.read()
    if not validate_file_size(len(contents)):
        raise HTTPException(status_code=413, detail="File too large")

    job_id = uuid.uuid4().hex
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    ext = os.path.splitext(file.filename or "file.bin")[1].lower()
    input_path = os.path.join(str(job_dir), f"input{ext}")
    output_path = os.path.join(str(job_dir), f"cleaned{ext}")

    with open(input_path, "wb") as f:
        f.write(contents)

    try:
        clean_metadata(input_path, output_path)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Metadata cleaning failed: {e}")

    return FileResponse(output_path, filename=f"cleaned{ext}", media_type="application/octet-stream")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": f"Внутренняя ошибка сервера: {exc}"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
