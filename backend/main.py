import os
import logging
import uuid
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.converters import ImageConverter, AudioConverter, VideoConverter, DocumentConverter
from backend.utils import (
    validate_file_size, validate_extension, get_category,
    cleanup_uploads, MAX_FILE_SIZE_BYTES,
)

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
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.post("/api/convert")
async def convert_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_format: str = Form(...),
):
    ext = os.path.splitext(file.filename or "")[1].lstrip(".").lower()
    logger.info(f"Received file: {file.filename}, target: {target_format}")

    if not validate_extension(ext):
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: .{ext}")

    contents = await file.read()
    if not validate_file_size(len(contents)):
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {MAX_FILE_SIZE_BYTES // (1024*1024)} MB",
        )

    category = get_category(ext)
    converter = converters.get(category)
    if not converter:
        raise HTTPException(status_code=400, detail=f"No converter for category: {category}")

    conv_map = converter.supported_conversions()
    if ext not in conv_map or target_format not in conv_map[ext]:
        raise HTTPException(
            status_code=400,
            detail=f"Conversion from .{ext} to .{target_format} is not supported",
        )

    job_id = uuid.uuid4().hex
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    input_path = job_dir / f"input.{ext}"
    with open(input_path, "wb") as f:
        f.write(contents)

    try:
        output_path = converter.convert(str(input_path), target_format, str(job_dir))
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    background_tasks.add_task(cleanup_uploads, str(UPLOAD_DIR))

    return FileResponse(
        output_path,
        filename=os.path.basename(output_path),
        media_type="application/octet-stream",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
