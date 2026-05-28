import os
import logging
from PIL import Image
from PIL.ExifTags import TAGS

logger = logging.getLogger("hidconverter")

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".ico", ".tiff", ".tif"}


def clean_metadata(file_path: str, output_path: str = None) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext in IMAGE_EXTS:
        return _clean_image_metadata(file_path, output_path)

    logger.info(f"No metadata cleaning implemented for {ext}, returning original")
    return output_path or file_path


def _clean_image_metadata(file_path: str, output_path: str = None) -> str:
    if output_path is None:
        base, ext = os.path.splitext(file_path)
        output_path = f"{base}_cleaned{ext}"

    img = Image.open(file_path)
    img = img.convert("RGB") if img.mode in ("RGBA", "P") else img

    data = list(img.getdata())
    img_clean = Image.new(img.mode, img.size)
    img_clean.putdata(data)

    save_kwargs = {}
    ext = os.path.splitext(output_path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        save_kwargs["quality"] = 95
        save_kwargs["optimize"] = True
    elif ext == ".webp":
        save_kwargs["quality"] = 90
    elif ext == ".png":
        save_kwargs["optimize"] = True

    img_clean.save(output_path, **save_kwargs)
    logger.info(f"Metadata stripped from {file_path} -> {output_path}")
    return output_path
