"""Allow ``python -m enhanced_youtube_downloader``."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
