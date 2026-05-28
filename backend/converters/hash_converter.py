import os
import hashlib
import logging
from typing import Dict, List

from .base import BaseConverter

logger = logging.getLogger("hidconverter")


def _hash_file(file_path: str) -> Dict[str, str]:
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            md5.update(chunk)
            sha1.update(chunk)
            sha256.update(chunk)
    return {
        "md5": md5.hexdigest(),
        "sha1": sha1.hexdigest(),
        "sha256": sha256.hexdigest(),
    }


class HashConverter(BaseConverter):
    SUPPORTED = {
        "hash": ["md5", "sha1", "sha256"],
    }

    def supported_conversions(self) -> Dict[str, List[str]]:
        return self.SUPPORTED

    def convert(self, file_path: str, target_format: str, output_dir: str, **kwargs) -> str:
        hashes = _hash_file(file_path)
        output_path = os.path.join(output_dir, "hashes.json")

        import json
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(hashes, f, indent=2)
        return output_path

    @staticmethod
    def compute_hashes(file_path: str) -> Dict[str, str]:
        return _hash_file(file_path)

    @staticmethod
    def compute_text_hashes(text: str) -> Dict[str, str]:
        data = text.encode("utf-8")
        return {
            "md5": hashlib.md5(data).hexdigest(),
            "sha1": hashlib.sha1(data).hexdigest(),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
