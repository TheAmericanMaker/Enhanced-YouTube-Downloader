"""Enhanced YouTube downloader built on yt-dlp."""

from .downloader import DownloadResult, YouTubeDownloader, validate_url
from .options import (
    AUDIO_FORMATS,
    BROWSERS,
    DEFAULT_FILENAME_TEMPLATE,
    DownloadOptions,
    QualityError,
    cookie_browser_to_tuple,
    format_selector,
    parse_browser,
    parse_langs,
    parse_quality,
)

__version__ = "0.2.0"

__all__ = [
    "AUDIO_FORMATS",
    "BROWSERS",
    "DEFAULT_FILENAME_TEMPLATE",
    "DownloadOptions",
    "DownloadResult",
    "QualityError",
    "YouTubeDownloader",
    "__version__",
    "cookie_browser_to_tuple",
    "format_selector",
    "parse_browser",
    "parse_langs",
    "parse_quality",
    "validate_url",
]
