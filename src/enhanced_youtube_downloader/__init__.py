"""Enhanced YouTube downloader built on yt-dlp."""

from .downloader import DownloadResult, YouTubeDownloader, validate_url
from .options import (
    AUDIO_FORMATS,
    DEFAULT_FILENAME_TEMPLATE,
    DownloadOptions,
    QualityError,
    format_selector,
    parse_langs,
    parse_quality,
)

__version__ = "0.1.0"

__all__ = [
    "AUDIO_FORMATS",
    "DEFAULT_FILENAME_TEMPLATE",
    "DownloadOptions",
    "DownloadResult",
    "QualityError",
    "YouTubeDownloader",
    "__version__",
    "format_selector",
    "parse_langs",
    "parse_quality",
    "validate_url",
]
