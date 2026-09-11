"""Download configuration for the enhanced YouTube downloader."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

__all__ = [
    "AUDIO_FORMATS",
    "DEFAULT_FILENAME_TEMPLATE",
    "DownloadOptions",
    "QualityError",
    "format_selector",
    "parse_langs",
    "parse_quality",
]

DEFAULT_FILENAME_TEMPLATE = "%(title)s [%(id)s].%(ext)s"

AUDIO_FORMATS = frozenset(
    {"aac", "alac", "best", "flac", "m4a", "mp3", "opus", "vorbis", "wav", "wma"}
)

_HEIGHT_RE = re.compile(r"^(\d+)p$")
_SPECIAL_QUALITIES = ("best", "worst")
_MIN_HEIGHT = 144


class QualityError(ValueError):
    """Raised when a quality specification is invalid."""


def parse_quality(quality: str) -> str:
    """Normalize and validate a quality spec.

    Accepts ``best``, ``worst``, or ``<height>p`` (e.g. ``1080p``).

    Args:
        quality: raw quality specification from the user.

    Returns:
        The normalized lowercase spec (e.g. ``"1080p"``).

    Raises:
        QualityError: if the spec is not recognized.
    """
    if not isinstance(quality, str):
        raise QualityError(f"quality must be a string, got {type(quality).__name__}")
    normalized = quality.strip().lower()
    if normalized in _SPECIAL_QUALITIES:
        return normalized
    match = _HEIGHT_RE.fullmatch(normalized)
    if match:
        height = int(match.group(1))
        if height < _MIN_HEIGHT:
            raise QualityError(f"height must be at least {_MIN_HEIGHT}p, got {normalized!r}")
        return normalized
    raise QualityError(
        f"invalid quality {quality!r}; use 'best', 'worst', or '<height>p' (e.g. '1080p')"
    )


def format_selector(quality: str) -> str:
    """Build the yt-dlp format selector for a quality spec.

    Args:
        quality: a spec accepted by :func:`parse_quality`.

    Returns:
        A yt-dlp format string, e.g. ``bestvideo[height<=720]+bestaudio``.
    """
    normalized = parse_quality(quality)
    if normalized == "best":
        return "bestvideo+bestaudio/best"
    if normalized == "worst":
        return "worst"
    height = int(normalized[:-1])
    return f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"


def parse_langs(spec: str) -> list[str]:
    """Parse a comma/space separated language list (e.g. ``"en, de"``)."""
    return [part.strip() for part in re.split(r"[,\s]+", spec.strip()) if part.strip()]


@dataclass
class DownloadOptions:
    """User-facing download configuration with sensible defaults."""

    quality: str = "best"
    output_path: str | None = None
    audio_only: bool = False
    audio_format: str = "mp3"
    audio_quality: str = "192"
    download_thumbnails: bool = False
    download_subtitles: bool = False
    subtitle_languages: list[str] = field(default_factory=lambda: ["en"])
    playlist: bool = False
    playlist_items: str | None = None
    retries: int = 3
    embed_metadata: bool = True
    filename_template: str = DEFAULT_FILENAME_TEMPLATE

    def validate(self) -> DownloadOptions:
        """Validate every field and return ``self`` for chaining.

        Raises:
            ValueError: if any field is invalid (including :class:`QualityError`).
        """
        parse_quality(self.quality)
        if self.audio_only and self.audio_format not in AUDIO_FORMATS:
            valid = ", ".join(sorted(AUDIO_FORMATS))
            raise ValueError(
                f"unsupported audio format {self.audio_format!r}; choose from: {valid}"
            )
        if self.retries < 1:
            raise ValueError(f"retries must be at least 1, got {self.retries}")
        if not self.filename_template.strip():
            raise ValueError("filename_template must not be empty")
        if self.download_subtitles and not self.subtitle_languages:
            raise ValueError("subtitle_languages must not be empty when downloading subtitles")
        return self
