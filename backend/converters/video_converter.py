import os
import asyncio
import logging
from typing import Dict, List
from .base import BaseConverter

logger = logging.getLogger("hidconverter")


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

    def supported_conversions(self) -> Dict[str, List[str]]:
        return self.SUPPORTED

    async def convert(self, file_path: str, target_format: str, output_dir: str, **kwargs) -> str:
        ext = os.path.splitext(file_path)[1].lstrip(".").lower()
        if ext not in self.SUPPORTED or target_format not in self.SUPPORTED[ext]:
            raise ValueError(f"Conversion from {ext} to {target_format} is not supported")

        output_path = self.get_output_path(file_path, target_format, output_dir)

        if target_format == "mp3":
            cmd = [
                "ffmpeg", "-y",
                "-i", file_path,
                "-vn",
            ]
            bitrate = kwargs.get("bitrate")
            if bitrate:
                cmd.extend(["-b:a", str(bitrate)])
            cmd.extend(["-loglevel", "error", output_path])
        else:
            vcodec = self.VIDEO_CODEC_MAP.get(target_format, "libx264")
            cmd = [
                "ffmpeg", "-y",
                "-i", file_path,
                "-vcodec", vcodec,
                "-acodec", "aac",
            ]
            bitrate = kwargs.get("bitrate")
            if bitrate:
                cmd.extend(["-b:a", str(bitrate)])
            cmd.extend(["-loglevel", "error", output_path])

        logger.info(f"Running: {' '.join(cmd)}")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()

        if process.returncode != 0:
            error_text = stderr.decode().strip() if stderr else "Unknown FFmpeg error"
            raise RuntimeError(f"FFmpeg error: {error_text}")

        return output_path
