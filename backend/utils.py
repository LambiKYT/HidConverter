import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger("hidconverter")

MAX_FILE_SIZE_MB = 200
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

ALLOWED_EXTENSIONS = {
    # images
    "png", "jpg", "jpeg", "webp", "bmp", "gif", "ico",
    # audio
    "mp3", "wav", "ogg", "flac", "m4a", "aac",
    # video
    "mp4", "avi", "mkv", "mov", "webm",
    # documents
    "pdf", "docx", "txt", "md", "xlsx", "csv",
    # data
    "json", "yaml", "yml", "xml",
}

FILE_CATEGORIES = {
    "image": {"png", "jpg", "jpeg", "webp", "bmp", "gif", "ico"},
    "audio": {"mp3", "wav", "ogg", "flac", "m4a", "aac"},
    "video": {"mp4", "avi", "mkv", "mov", "webm"},
    "document": {"pdf", "docx", "txt", "md", "xlsx", "csv"},
    "data": {"json", "yaml", "yml", "xml"},
}


def get_category(ext: str) -> str:
    ext = ext.lstrip(".").lower()
    for category, exts in FILE_CATEGORIES.items():
        if ext in exts:
            return category
    return "unknown"


def validate_file_size(size: int) -> bool:
    return size <= MAX_FILE_SIZE_BYTES


def validate_extension(ext: str) -> bool:
    return ext.lstrip(".").lower() in ALLOWED_EXTENSIONS


def cleanup_uploads(upload_dir: str):
    try:
        path = Path(upload_dir)
        if path.exists():
            for item in path.iterdir():
                if item.is_file():
                    item.unlink(missing_ok=True)
                elif item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
        logger.info("Upload directory cleaned")
    except Exception as e:
        logger.warning(f"Cleanup error: {e}")
