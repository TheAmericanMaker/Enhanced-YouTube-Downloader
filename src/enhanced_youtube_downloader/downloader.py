"""Core download engine built on yt-dlp."""

from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import yt_dlp

from .options import DownloadOptions, format_selector
from .progress import ProgressBar

logger = logging.getLogger(__name__)

__all__ = ["DownloadResult", "YouTubeDownloader", "validate_url"]


@dataclass
class DownloadResult:
    """Outcome of a download attempt."""

    ok: bool
    requested_url: str
    filename: str | None = None
    error: str | None = None


def validate_url(url: str) -> str:
    """Sanitize and sanity-check a URL.

    Args:
        url: the URL to check.

    Returns:
        The stripped URL.

    Raises:
        ValueError: if the URL is not a string, is empty, or is not http(s).
    """
    if not isinstance(url, str):
        raise ValueError(f"URL must be a string, got {type(url).__name__}")
    candidate = url.strip()
    parsed = urlparse(candidate)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"unsupported URL scheme {parsed.scheme!r}; expected http or https")
    if not parsed.netloc:
        raise ValueError(f"URL has no host: {candidate!r}")
    return candidate


class YouTubeDownloader:
    """High-level wrapper around yt-dlp.

    Args:
        verbose: when True, yt-dlp warnings and debug output are surfaced.
        progress: when True, a tqdm progress bar is shown during downloads.
    """

    def __init__(self, *, verbose: bool = False, progress: bool = True) -> None:
        self.verbose = verbose
        self.progress_enabled = progress

    def get_video_info(self, url: str, *, playlist: bool = False) -> dict[str, Any] | None:
        """Fetch metadata for a video or playlist without downloading.

        Returns:
            The yt-dlp info dict, or None on failure.
        """
        validate_url(url)
        params: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        if playlist:
            params["extract_flat"] = "in_playlist"
        try:
            with yt_dlp.YoutubeDL(params) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as exc:
            logger.error("Failed to fetch info for %s: %s", url, exc)
            return None

    def list_formats(self, url: str) -> list[dict[str, Any]]:
        """List all available formats for a video. Returns [] on failure."""
        info = self.get_video_info(url) or {}
        formats = info.get("formats") or []
        return list(formats)

    def build_ydl_options(self, options: DownloadOptions) -> dict[str, Any]:
        """Translate :class:`DownloadOptions` into yt-dlp parameter dict.

        Raises:
            ValueError: if the options are invalid (see :meth:`DownloadOptions.validate`).
            PermissionError: if the output directory is not writable.
        """
        options.validate()

        outtmpl = options.filename_template
        if options.playlist:
            outtmpl = "%(playlist_title,playlist,uploader)s/" + outtmpl
        if options.output_path:
            outdir = os.path.abspath(os.path.expanduser(options.output_path))
            os.makedirs(outdir, exist_ok=True)
            if not os.access(outdir, os.W_OK):
                raise PermissionError(f"output directory is not writable: {outdir}")
            outtmpl = os.path.join(outdir, outtmpl)

        opts: dict[str, Any] = {
            "format": "bestaudio/best" if options.audio_only else format_selector(options.quality),
            "outtmpl": outtmpl,
            "quiet": not self.verbose,
            "no_warnings": not self.verbose,
            "noprogress": True,
            "retries": options.retries,
            "embedmetadata": options.embed_metadata,
            "ignoreerrors": options.playlist,
            "noplaylist": not options.playlist,
        }

        if options.audio_only:
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": options.audio_format,
                    "preferredquality": options.audio_quality,
                }
            ]

        if options.download_subtitles:
            opts["writesubtitles"] = True
            opts["subtitleslangs"] = list(options.subtitle_languages)
            if not options.audio_only:
                opts.setdefault("postprocessors", []).append({"key": "FFmpegEmbedSubtitle"})

        if options.download_thumbnails:
            opts["writethumbnail"] = True
            if not options.audio_only:
                opts["embedthumbnail"] = True
                opts.setdefault("postprocessors", []).append(
                    {"key": "FFmpegThumbnailsConvertor", "format": "jpg"}
                )

        if options.playlist and options.playlist_items:
            opts["playlist_items"] = options.playlist_items

        return opts

    def download(self, url: str, options: DownloadOptions | None = None) -> DownloadResult:
        """Download a video (or whole playlist) with the given options.

        Args:
            url: the video or playlist URL.
            options: download configuration; defaults are used when omitted.

        Returns:
            A :class:`DownloadResult`. Validation errors are raised
            immediately instead of being returned.
        """
        options = (options or DownloadOptions()).validate()
        validate_url(url)

        needs_ffmpeg = (
            options.audio_only or options.download_subtitles or options.download_thumbnails
        )
        if needs_ffmpeg and shutil.which("ffmpeg") is None:
            logger.warning(
                "ffmpeg was not found on PATH; audio extraction, subtitle embedding, "
                "and thumbnail conversion will fail"
            )

        ydl_opts = self.build_ydl_options(options)
        finished: list[str] = []

        def track_finished(filename: str) -> None:
            # post_hooks fire after post-processing, so the filename is final.
            if filename:
                finished.append(filename)

        bar = ProgressBar(enabled=self.progress_enabled)
        ydl_opts["progress_hooks"] = [bar.hook]
        ydl_opts["post_hooks"] = [track_finished]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return DownloadResult(
                ok=True,
                requested_url=url,
                filename=finished[-1] if finished else None,
            )
        except Exception as exc:
            logger.error("Download failed for %s: %s", url, exc)
            return DownloadResult(ok=False, requested_url=url, error=str(exc))
        finally:
            bar.close()
