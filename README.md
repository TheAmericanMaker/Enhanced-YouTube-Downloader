# Enhanced YouTube Downloader

A fast, feature-rich command-line YouTube downloader built on
[yt-dlp](https://github.com/yt-dlp/yt-dlp). Download videos in any quality,
extract audio to MP3/Opus/FLAC and more, grab whole playlists, and pull
subtitles and thumbnails — from a clean CLI, an interactive shell, or a small
Python API.

> [!IMPORTANT]
> Only download content you have the rights to. Respect YouTube's Terms of
> Service and the copyright laws of your jurisdiction. This project is
> provided for personal, lawful use.

## Features

- **Quality selection** — `best`, `worst`, or an exact height cap (`1080p`, `720p`, ...)
- **Audio extraction** — MP3, Opus, AAC, FLAC, and more with configurable VBR quality
- **Playlist support** — whole playlists or selected items (`--playlist-items 1-5,8`)
- **Subtitles** — download (and embed) one or more languages
- **Thumbnails** — download as JPG and embed into the video
- **Metadata** — embedded by default, opt out with `--no-embed-metadata`
- **Format browser** — `eyd formats <url>` prints a table of every available format
- **Progress bar** — live progress via [tqdm](https://github.com/tqdm/tqdm)
- **Retry logic** — configurable network retries per file
- **Python API** — import `YouTubeDownloader` and `DownloadOptions` into your own scripts

## Installation

### From PyPI

```console
$ pipx install enhanced-youtube-downloader   # or: pip install enhanced-youtube-downloader
```

### From source

```console
$ git clone https://github.com/TheAmericanMaker/Enhanced-YouTube-Downloader.git
$ cd Enhanced-YouTube-Downloader
$ pip install -e ".[dev]"
```

### FFmpeg

[FFmpeg](https://ffmpeg.org/) is required for audio extraction, subtitle
embedding, and thumbnail conversion:

| Platform        | Command                          |
| --------------- | -------------------------------- |
| macOS           | `brew install ffmpeg`            |
| Debian / Ubuntu | `sudo apt install ffmpeg`        |
| Fedora / RHEL   | `sudo dnf install ffmpeg`        |
| Windows         | `winget install Gyan.FFmpeg`     |

## Usage

```console
$ eyd --help
```

### Download a video

```console
$ eyd download "https://www.youtube.com/watch?v=..." -q 1080p
$ eyd download "https://www.youtube.com/watch?v=..." -q best -o ~/Videos
```

### Extract audio

```console
$ eyd audio "https://www.youtube.com/watch?v=..."              # MP3 (192 kbps)
$ eyd audio "https://www.youtube.com/watch?v=..." -f opus --audio-quality 128
```

### List formats

```console
$ eyd formats "https://www.youtube.com/watch?v=..."
Format Ext Resolution FPS     Size      Note
137    mp4 1080p      30      24.3 MiB
251    webm audio only            2.9 MiB
...
```

### Show metadata

```console
$ eyd info "https://www.youtube.com/watch?v=..."
Title    : ...
Channel  : ...
Duration : 12:34
Views    : 12345
```

### Playlists and extras

```console
$ eyd download "https://www.youtube.com/playlist?list=..." --playlist
$ eyd download "https://www.youtube.com/playlist?list=..." --playlist --playlist-items 1-5,8
$ eyd download "https://www.youtube.com/watch?v=..." --subtitles --subtitle-langs en,de --thumbnails
```

### Options

| Flag | Meaning |
| ---- | ------- |
| `-q, --quality` | `best` (default), `worst`, or `<height>p` |
| `-o, --output DIR` | Output directory (default: current directory) |
| `-f, --audio-format` | Audio codec: `mp3`, `opus`, `aac`, `flac`, `m4a`, `wav`, `vorbis`, `alac`, `wma`, `best` |
| `--audio-quality` | VBR bitrate for audio (default: `192`) |
| `--subtitles` / `--subtitle-langs` | Download subtitles for the given languages (default: `en`) |
| `--thumbnails` | Download the thumbnail (embedded for videos) |
| `--no-embed-metadata` | Don't embed metadata |
| `--playlist` / `--playlist-items` | Whole playlist / item range like `1-5,8` |
| `--filename-template` | Custom [yt-dlp output template](https://github.com/yt-dlp/yt-dlp/blob/master/README.md#output-template) |
| `--retries` | Network retries per file (default: 3) |
| `--no-progress` | Disable the progress bar |
| `-v, --verbose` | Debug output |

### Interactive mode

```console
$ eyd interactive
Enhanced YouTube Downloader - interactive mode
Type 'help' for a list of commands, 'quit' to exit.

eyd> download https://www.youtube.com/watch?v=... 1080p
```

Commands: `download`, `audio`, `formats`, `info`, `dir [path]`, `help`, `quit`.

## Library usage

```python
from enhanced_youtube_downloader import DownloadOptions, YouTubeDownloader

downloader = YouTubeDownloader(progress=True)
options = DownloadOptions(
    quality="720p",
    output_path="~/Videos",
    download_subtitles=True,
    subtitle_languages=["en", "de"],
)
result = downloader.download("https://www.youtube.com/watch?v=...", options)
if result.ok:
    print("Saved:", result.filename)
else:
    print("Failed:", result.error)
```

## Project layout

```
src/enhanced_youtube_downloader/
├── __init__.py       # public API + version
├── __main__.py       # python -m entry point
├── cli.py            # argparse CLI (download, audio, formats, info, interactive)
├── downloader.py     # YouTubeDownloader, DownloadResult, URL validation
├── options.py        # DownloadOptions, quality/audio validation
└── progress.py       # tqdm progress bar
tests/                # pytest suite (yt-dlp mocked, no network needed)
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for the
development setup, code style, and PR process. Please also read the
[Code of Conduct](.github/CODE_OF_CONDUCT.md).

## Security

See [SECURITY.md](SECURITY.md) for how to report vulnerabilities.

## License

[MIT](LICENSE) — see the [LICENSE](LICENSE) file.
