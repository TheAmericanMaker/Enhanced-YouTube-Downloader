# Contributing

Thanks for your interest in contributing to Enhanced YouTube Downloader!
This project welcomes bug reports, feature requests, documentation fixes,
and code contributions of all kinds.

## Ground rules

- Please search existing issues before opening a new one.
- Be kind and constructive in issues and pull requests.
- Contributions are expected to follow the [Code of Conduct](.github/CODE_OF_CONDUCT.md).

## Development setup

Python 3.9 or newer is required.

```bash
git clone https://github.com/TheAmericanMaker/Enhanced-YouTube-Downloader.git
cd Enhanced-YouTube-Downloader
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

This installs the package in editable mode with the `eyd` command available,
plus development tools (pytest, ruff, pytest-cov).

> **Note:** audio extraction, subtitle embedding, and thumbnails also require
> [FFmpeg](https://ffmpeg.org/) on your `PATH`.

## Code style

We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
ruff check src tests        # lint
ruff format src tests       # format
```

Configuration lives in `pyproject.toml`. Run both before submitting a PR.

## Running tests

```bash
pytest
```

Tests must not require network access or FFmpeg; yt-dlp is mocked
(see `tests/conftest.py`). If you add a feature, add or adjust tests for it.

## Pull requests

1. Fork the repository and create a topic branch from `main`.
2. Keep PRs small and focused; one feature or fix per PR.
3. Add tests for new behavior.
4. Update `CHANGELOG.md` with a short entry under the appropriate heading.
5. Make sure `ruff check`, `ruff format --check`, and `pytest` all pass.
6. Open the PR and fill in the template.

## Release process (maintainers)

- Bump `version` in `pyproject.toml` (and `__version__` in
  `src/enhanced_youtube_downloader/__init__.py`).
- Update `CHANGELOG.md`.
- Tag the release as `vX.Y.Z`; the GitHub Actions workflow builds the
  package and publishes it to PyPI via trusted publishing.

## Legal

This tool wraps [yt-dlp](https://github.com/yt-dlp/yt-dlp) and downloads
content from YouTube. By using it (or contributing to it) you agree that:

- You will only download content you have the right to download.
- You will comply with YouTube's Terms of Service and the laws of your
  jurisdiction.
- The project and its contributors are not liable for misuse.
