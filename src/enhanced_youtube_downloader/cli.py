"""Command-line interface for the enhanced YouTube downloader."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections.abc import Sequence

from . import __version__
from .downloader import DownloadResult, YouTubeDownloader
from .options import AUDIO_FORMATS, DEFAULT_FILENAME_TEMPLATE, DownloadOptions, parse_langs

logger = logging.getLogger(__name__)

__all__ = ["build_parser", "main"]


def _human_size(value: float | None) -> str:
    if value is None:
        return ""
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            if unit == "B":
                return f"{size:.0f} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return ""


def _format_duration(seconds: float | None) -> str:
    if not seconds:
        return "n/a"
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _print_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
    widths = [len(header) for header in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    print("  ".join(str(header).ljust(widths[i]) for i, header in enumerate(headers)))
    for row in rows:
        print("  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)))


def _run_download(args: argparse.Namespace, options: DownloadOptions) -> DownloadResult:
    downloader = YouTubeDownloader(verbose=args.verbose, progress=not args.no_progress)
    return downloader.download(args.url, options)


def _report_result(result: DownloadResult) -> int:
    if result.ok:
        if result.filename:
            print(f"Saved: {result.filename}")
        else:
            print("Download completed.")
        return 0
    print(f"error: {result.error}", file=sys.stderr)
    return 1


def cmd_download(args: argparse.Namespace) -> int:
    options = DownloadOptions(
        quality=args.quality,
        output_path=args.output,
        download_subtitles=args.subtitles,
        subtitle_languages=parse_langs(args.subtitle_langs) if args.subtitles else [],
        download_thumbnails=args.thumbnails,
        playlist=args.playlist,
        playlist_items=args.playlist_items,
        retries=args.retries,
        embed_metadata=not args.no_embed_metadata,
        filename_template=args.filename_template or DEFAULT_FILENAME_TEMPLATE,
    )
    return _report_result(_run_download(args, options))


def cmd_audio(args: argparse.Namespace) -> int:
    options = DownloadOptions(
        output_path=args.output,
        audio_only=True,
        audio_format=args.audio_format,
        audio_quality=args.audio_quality,
        download_subtitles=args.subtitles,
        subtitle_languages=parse_langs(args.subtitle_langs) if args.subtitles else [],
        playlist=args.playlist,
        playlist_items=args.playlist_items,
        retries=args.retries,
        embed_metadata=not args.no_embed_metadata,
        filename_template=args.filename_template or DEFAULT_FILENAME_TEMPLATE,
    )
    return _report_result(_run_download(args, options))


def cmd_formats(args: argparse.Namespace) -> int:
    downloader = YouTubeDownloader(progress=False)
    formats = downloader.list_formats(args.url)
    if not formats:
        print("No formats found. Check the URL and try again.", file=sys.stderr)
        return 1
    rows = []
    for fmt in formats:
        rows.append(
            (
                str(fmt.get("format_id", "?")),
                str(fmt.get("ext", "?")),
                fmt.get("resolution") or "audio only",
                str(fmt.get("fps") or ""),
                _human_size(fmt.get("filesize") or fmt.get("filesize_approx")),
                fmt.get("note") or "",
            )
        )
    _print_table(("Format", "Ext", "Resolution", "FPS", "Size", "Note"), rows)
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    downloader = YouTubeDownloader(progress=False)
    info = downloader.get_video_info(args.url, playlist=args.playlist)
    if info is None:
        print("Could not fetch information. Check the URL and try again.", file=sys.stderr)
        return 1
    if info.get("_type") == "playlist":
        entries = [entry for entry in (info.get("entries") or []) if entry]
        print(f"Playlist : {info.get('title', 'unknown')}")
        print(f"Entries  : {len(entries)}")
        for entry in entries:
            print(
                f"  {entry.get('id', '?'):<12} "
                f"{_format_duration(entry.get('duration')):>8}  "
                f"{entry.get('title', 'untitled')}"
            )
    else:
        print(f"Title    : {info.get('title', 'unknown')}")
        print(f"Channel  : {info.get('uploader') or info.get('channel') or 'unknown'}")
        print(f"Duration : {_format_duration(info.get('duration'))}")
        print(f"Views    : {info.get('view_count', 'n/a')}")
        print(f"URL      : {info.get('webpage_url') or args.url}")
    return 0


_REPL_HELP = """\
Available commands:
  download <url> [quality]  Download a video (quality: best, worst, <height>p)
  audio <url>               Download the audio track (MP3)
  formats <url>             List available formats
  info <url>                Show video metadata
  dir [path]                Show or set the output directory
  help                      Show this help
  quit                      Exit
"""


def cmd_interactive(args: argparse.Namespace) -> int:
    """Run the interactive shell (original REPL behavior, ported)."""
    downloader = YouTubeDownloader(verbose=args.verbose, progress=not args.no_progress)
    state = {"output": args.output or os.path.expanduser("~/Downloads")}

    print("Enhanced YouTube Downloader - interactive mode")
    print("Type 'help' for a list of commands, 'quit' to exit.")

    while True:
        try:
            raw = input("\neyd> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not raw:
            continue
        parts = raw.split(maxsplit=1)
        command = parts[0].lower()
        rest = parts[1].strip() if len(parts) > 1 else ""
        try:
            if command in ("quit", "exit"):
                break
            elif command == "help":
                print(_REPL_HELP)
            elif command == "dir":
                if rest:
                    state["output"] = os.path.abspath(os.path.expanduser(rest))
                print(f"Output directory: {state['output']}")
            elif command in ("download", "audio"):
                if not rest:
                    print(f"usage: {command} <url> [quality]")
                    continue
                pieces = rest.split(maxsplit=1)
                url = pieces[0]
                quality = pieces[1].strip() if len(pieces) > 1 else "best"
                options = DownloadOptions(
                    quality=quality if command == "download" else "best",
                    output_path=state["output"],
                    audio_only=command == "audio",
                )
                result = downloader.download(url, options)
                print("Download completed." if result.ok else f"Download failed: {result.error}")
            elif command == "formats":
                if not rest:
                    print("usage: formats <url>")
                    continue
                for fmt in downloader.list_formats(rest):
                    resolution = fmt.get("resolution") or "audio"
                    print(
                        f"format {fmt.get('format_id', '?')}: {resolution} / {fmt.get('ext', '?')}"
                    )
            elif command == "info":
                if not rest:
                    print("usage: info <url>")
                    continue
                info = downloader.get_video_info(rest)
                if info is None:
                    print("Could not fetch info.")
                else:
                    print(f"Title  : {info.get('title')}")
                    print(f"Channel: {info.get('uploader') or info.get('channel')}")
            else:
                print("Unknown command. Type 'help' for usage.")
        except Exception as exc:
            print(f"Error: {exc}")
    return 0


def _add_common_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        metavar="DIR",
        help="output directory (default: current directory)",
    )
    parser.add_argument(
        "--filename-template",
        default=None,
        metavar="TEMPLATE",
        help=f"yt-dlp filename template (default: {DEFAULT_FILENAME_TEMPLATE.replace('%', '%%')})",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="network retries per file (default: 3)",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="disable the progress bar",
    )


def _add_media_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--subtitles",
        action="store_true",
        help="download subtitles",
    )
    parser.add_argument(
        "--subtitle-langs",
        default="en",
        metavar="LANGS",
        help="comma separated subtitle languages (default: en)",
    )
    parser.add_argument(
        "--thumbnails",
        action="store_true",
        help="download the thumbnail (and embed it for videos)",
    )
    parser.add_argument(
        "--no-embed-metadata",
        action="store_true",
        help="do not embed metadata in the file",
    )
    parser.add_argument(
        "--playlist",
        action="store_true",
        help="download the whole playlist the URL belongs to",
    )
    parser.add_argument(
        "--playlist-items",
        default=None,
        metavar="RANGE",
        help="playlist item range, e.g. '1-5,8'",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the ``eyd`` command."""
    parser = argparse.ArgumentParser(
        prog="eyd",
        description="Enhanced YouTube downloader built on yt-dlp.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="enable debug output")

    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    common = argparse.ArgumentParser(add_help=False)
    _add_common_flags(common)
    media = argparse.ArgumentParser(add_help=False)
    _add_media_flags(media)

    p = subparsers.add_parser("download", parents=[common, media], help="download a video")
    p.add_argument("url", help="YouTube video or playlist URL")
    p.add_argument(
        "-q",
        "--quality",
        default="best",
        help="'best', 'worst', or '<height>p' (default: best)",
    )
    p.set_defaults(func=cmd_download)

    p = subparsers.add_parser("audio", parents=[common, media], help="extract audio only")
    p.add_argument("url", help="YouTube video or playlist URL")
    p.add_argument(
        "-f",
        "--audio-format",
        default="mp3",
        choices=sorted(AUDIO_FORMATS),
        help="audio codec/container (default: mp3)",
    )
    p.add_argument(
        "--audio-quality",
        default="192",
        help="VBR bitrate for the extracted audio (default: 192)",
    )
    p.set_defaults(func=cmd_audio)

    p = subparsers.add_parser("formats", parents=[common], help="list available formats")
    p.add_argument("url", help="YouTube video URL")
    p.set_defaults(func=cmd_formats)

    p = subparsers.add_parser("info", parents=[common], help="show video or playlist metadata")
    p.add_argument("url", help="YouTube video or playlist URL")
    p.add_argument("--playlist", action="store_true", help="treat the URL as a playlist")
    p.set_defaults(func=cmd_info)

    p = subparsers.add_parser("interactive", parents=[common], help="start the interactive shell")
    p.set_defaults(func=cmd_interactive)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except (ValueError, PermissionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
