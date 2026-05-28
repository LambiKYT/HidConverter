import os
from typing import Dict, List
from PIL import Image
from .base import BaseConverter


class ImageConverter(BaseConverter):
    SUPPORTED = {
        "png":  ["jpg", "jpeg", "webp", "bmp", "gif", "ico", "png"],
        "jpg":  ["png", "webp", "bmp", "gif", "jpeg", "ico", "jpg"],
        "jpeg": ["png", "webp", "bmp", "gif", "jpg", "ico", "jpeg"],
        "webp": ["png", "jpg", "jpeg", "bmp", "gif", "ico", "webp"],
        "bmp":  ["png", "jpg", "jpeg", "webp", "gif", "ico", "bmp"],
        "gif":  ["png", "jpg", "jpeg", "webp", "bmp", "ico", "gif"],
        "ico":  ["png", "jpg", "jpeg", "webp", "bmp", "gif", "ico"],
    }

    def supported_conversions(self) -> Dict[str, List[str]]:
        return self.SUPPORTED

    def convert(self, file_path: str, target_format: str, output_dir: str, **kwargs) -> str:
        ext = os.path.splitext(file_path)[1].lstrip(".").lower()
        if ext not in self.SUPPORTED or target_format not in self.SUPPORTED[ext]:
            raise ValueError(f"Conversion from {ext} to {target_format} is not supported")

        with Image.open(file_path) as img:
            img = img.convert("RGBA") if target_format in ("png", "ico", "gif", "webp") else img.convert("RGB")

        output_path = self.get_output_path(file_path, target_format, output_dir)

        quality = kwargs.get("quality")
        if quality is not None:
            quality = max(1, min(100, int(quality)))

        save_kwargs = {}
        if target_format in ("jpg", "jpeg"):
            save_kwargs["quality"] = quality if quality else 92
            save_kwargs["optimize"] = True
        elif target_format == "webp":
            save_kwargs["quality"] = quality if quality else 85
            save_kwargs["method"] = 6
        elif target_format == "png":
            save_kwargs["optimize"] = True
        elif target_format == "ico" and ext != "ico":
            img = img.resize((256, 256), Image.LANCZOS)

        fmt_map = {"jpg": "JPEG", "jpeg": "JPEG", "tif": "TIFF", "tiff": "TIFF"}
        pil_format = fmt_map.get(target_format, target_format.upper())
        img.save(output_path, format=pil_format, **save_kwargs)
        return output_path
