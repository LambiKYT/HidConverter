import os
import subprocess
from typing import Dict, List
from .base import BaseConverter


class AudioConverter(BaseConverter):
    SUPPORTED = {
        "mp3":  ["wav", "ogg", "flac", "m4a", "aac", "mp3"],
        "wav":  ["mp3", "ogg", "flac", "m4a", "aac", "wav"],
        "ogg":  ["mp3", "wav", "flac", "m4a", "aac", "ogg"],
        "flac": ["mp3", "wav", "ogg", "m4a", "aac", "flac"],
        "m4a":  ["mp3", "wav", "ogg", "flac", "aac", "m4a"],
        "aac":  ["mp3", "wav", "ogg", "flac", "m4a", "aac"],
    }

    CODEC_MAP = {
        "mp3": "libmp3lame",
        "wav": "pcm_s16le",
        "ogg": "libvorbis",
        "flac": "flac",
        "m4a": "aac",
        "aac": "aac",
    }

    EXTENSION_MAP = {
        "mp3": "mp3",
        "wav": "wav",
        "ogg": "ogg",
        "flac": "flac",
        "m4a": "m4a",
        "aac": "aac",
    }

    def supported_conversions(self) -> Dict[str, List[str]]:
        return self.SUPPORTED

    def convert(self, file_path: str, target_format: str, output_dir: str) -> str:
        ext = os.path.splitext(file_path)[1].lstrip(".").lower()
        if ext not in self.SUPPORTED or target_format not in self.SUPPORTED[ext]:
            raise ValueError(f"Conversion from {ext} to {target_format} is not supported")

        output_path = self.get_output_path(file_path, target_format, output_dir)
        codec = self.CODEC_MAP.get(target_format, target_format)

        cmd = [
            "ffmpeg", "-y",
            "-i", file_path,
            "-acodec", codec,
            "-loglevel", "error",
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, shell=False)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg error: {result.stderr.strip()}")

        return output_path
