# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-05

First public release.

### Added

- Proper package layout (`src/enhanced_youtube_downloader`) with a
  `pyproject.toml` and an `eyd` console script (`python -m
  enhanced_youtube_downloader` also works).
- Argparse-based CLI with `download`, `audio`, `formats`, `info`, and
  `interactive` subcommands, replacing the REPL-only interface.
- Library API: `YouTubeDownloader`, `DownloadOptions`, and
  `DownloadResult` for embedding the downloader in your own scripts.
- `--subtitles/--subtitle-langs`, `--thumbnails`, `--filename-template`,
  `--retries`, `--playlist`, and `--playlist-items` flags.
- pytest test suite with a mocked yt-dlp backend (no network needed).
- GitHub Actions CI (ruff lint + tests on Python 3.9-3.13) and a
  PyPI publish workflow.
- LICENSE (MIT), CONTRIBUTING, code of conduct, issue/PR templates,
  and security policy.

### Changed

- Default filename template is now `%(title)s [%(id)s].%(ext)s` to avoid
  collisions between videos with identical titles.
- Playlist downloads now sort their output into a
  `<playlist title>/` subdirectory and map to real yt-dlp options
  (`noplaylist`/`playlist_items`/`ignoreerrors`).
- `best` quality now selects `bestvideo+bestaudio/best` so the highest
  available combined stream is preferred.

### Fixed

- Output paths containing `~` are expanded before use.
- Progress bar state is per-download instead of shared instance state,
  so interrupted or concurrent downloads no longer corrupt it.
- Progress updates use a tracked byte counter, fixing over/under-counting.
- The `--playlist` flag previously had no effect; it now works.
- Subtitle embedding is skipped for audio-only downloads (it would fail
  on audio containers).
- Non-http(s) URLs and invalid quality specs are rejected with clear
  errors instead of opaque yt-dlp tracebacks.

[0.1.0]: https://github.com/TheAmericanMaker/Enhanced-YouTube-Downloader/releases/tag/v0.1.0
