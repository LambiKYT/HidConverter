import os
import re
import shutil
import logging
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from typing import Optional

logger = logging.getLogger("hidconverter")

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


def download_from_url(url: str, output_dir: str, filename_hint: Optional[str] = None) -> str:
    logger.info(f"Downloading from URL: {url}")

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            },
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            content = response.read()
            content_type = response.headers.get("Content-Type", "")
            content_disposition = response.headers.get("Content-Disposition", "")

            filename = filename_hint or _extract_filename(url, content_disposition, content_type)
            dest = os.path.join(output_dir, filename)

            with open(dest, "wb") as f:
                f.write(content)

            logger.info(f"Downloaded {len(content)} bytes -> {dest}")
            return dest

    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.reason} for {url}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Download failed: {e}")


def _extract_filename(url: str, content_disposition: str, content_type: str) -> str:
    if content_disposition:
        match = re.search(r'filename[^;=\n]*=((["\']).*?\2|[^;\n]*)', content_disposition)
        if match:
            name = match.group(1).strip("\"'")
            if name:
                return name

    path = urllib.parse.urlparse(url).path
    basename = os.path.basename(path)
    if basename and "." in basename:
        return basename

    ext = _mime_to_ext(content_type)
    return f"downloaded{ext}"


def _mime_to_ext(mime: str) -> str:
    mime_map = {
        "image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif",
        "image/webp": ".webp", "image/bmp": ".bmp",
        "audio/mpeg": ".mp3", "audio/wav": ".wav", "audio/ogg": ".ogg",
        "audio/flac": ".flac",
        "video/mp4": ".mp4", "video/webm": ".webm",
        "application/pdf": ".pdf",
        "text/plain": ".txt", "text/html": ".html",
        "application/json": ".json",
        "application/zip": ".zip",
    }
    return mime_map.get(mime.split(";")[0].strip(), ".bin")


def download_youtube_audio(url: str, output_dir: str, target_format: str = "mp3") -> str:
    if yt_dlp is None:
        raise RuntimeError("Missing dependency: yt-dlp (pip install yt-dlp)")

    if target_format not in ("mp3", "wav"):
        target_format = "mp3"

    logger.info(f"Downloading YouTube audio: {url} -> {target_format}")

    tmp_dir = os.path.join(output_dir, "yt_tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(tmp_dir, "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": target_format,
                "preferredquality": "192",
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "audio")
            ext = target_format
            filename = f"{_sanitize_filename(title)}.{ext}"
            src = os.path.join(tmp_dir, filename)

            if not os.path.isfile(src):
                for f in os.listdir(tmp_dir):
                    if f.endswith(f".{ext}"):
                        src = os.path.join(tmp_dir, f)
                        break

            dest = os.path.join(output_dir, filename)
            if os.path.isfile(src):
                os.replace(src, dest)

            if os.path.isdir(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)

            logger.info(f"YouTube audio extracted -> {dest}")
            return dest

    except Exception as e:
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)
        raise RuntimeError(f"YouTube extraction failed: {e}")


def _sanitize_filename(name: str) -> str:
    invalid = r'[<>:"/\\|?*]'
    safe = re.sub(invalid, "_", name)
    return safe.strip() or "audio"
