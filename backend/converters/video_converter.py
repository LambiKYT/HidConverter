import os
import subprocess
from typing import Dict, List
from .base import BaseConverter


class VideoConverter(BaseConverter):
    SUPPORTED = {
        "mp4":  ["avi", "mkv", "mov", "webm", "mp3", "mp4"],
        "avi":  ["mp4", "mkv", "mov", "webm", "mp3", "avi"],
        "mkv":  ["mp4", "avi", "mov", "webm", "mp3", "mkv"],
        "mov":  ["mp4", "avi", "mkv", "webm", "mp3", "mov"],
        "webm": ["mp4", "avi", "mkv", "mov", "mp3", "webm"],
    }

    VIDEO_CODEC_MAP = {
        "mp4":  "libx264",
        "avi":  "mpeg4",
        "mkv":  "libx264",
        "mov":  "libx264",
        "webm": "libvpx",
    }

    AUDIO_CODEC_MAP = {
        "mp3": "libmp3lame",
    }

    def supported_conversions(self) -> Dict[str, List[str]]:
        return self.SUPPORTED

    def convert(self, file_path: str, target_format: str, output_dir: str) -> str:
        ext = os.path.splitext(file_path)[1].lstrip(".").lower()
        if ext not in self.SUPPORTED or target_format not in self.SUPPORTED[ext]:
            raise ValueError(f"Conversion from {ext} to {target_format} is not supported")

        output_path = self.get_output_path(file_path, target_format, output_dir)

        if target_format == "mp3":
            cmd = [
                "ffmpeg", "-y", "-i", file_path,
                "-vn", "-acodec", "libmp3lame",
                "-loglevel", "error",
                output_path
            ]
        else:
            vcodec = self.VIDEO_CODEC_MAP.get(target_format, "libx264")
            cmd = [
                "ffmpeg", "-y", "-i", file_path,
                "-vcodec", vcodec,
                "-acodec", "aac",
                "-loglevel", "error",
                output_path
            ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg error: {result.stderr.strip()}")

        return output_path
